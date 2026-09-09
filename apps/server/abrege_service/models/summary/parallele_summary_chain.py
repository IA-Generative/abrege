import os
import time
import json
from time import perf_counter
import traceback
import asyncio
import hashlib

from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from typing import Type, Union
from pydantic import BaseModel, Field
from langfuse import Langfuse, get_client
from langfuse.langchain import CallbackHandler


from src.schemas.result import SummaryModel, Text
from src.schemas.parameters import SummaryParameters
from src.schemas.task import TaskModel, TaskStatus, TaskUpdateForm, task_table
from src.clients import celery_app, redis_client
from src.utils.logger import logger_abrege


from abrege_service.models.base import BaseSummaryService
from abrege_service.models.summary.qa_chain import extract_leading_page_number
from abrege_service.utils.text import (
    split_texts_by_token_limit,
    sum_words,
    group_by_max_word_sum,
)

# Prompt pour l'étape de "map"
map_template = """The following is a set of documents:
{text}
Summarize concisely and clearly in paragraph form. Highlight the main ideas and recurring themes.
Respond ONLY with a valid JSON object matching this schema: {{"summary": "..."}}
Helpful Answer in {language}:"""

# Prompt pour l'étape de "reduce"
combine_template = """The following is a set of summaries:
{text}
Consolidate them into a clear and well-organized final summary. Highlight recurring ideas, themes, and insights. {prompt_size}.{custom_prompt}
Respond ONLY with a valid JSON object matching this schema: {{"summary": "..."}}
Helpful Answer in {language}:"""

# Prompt pour l'étape de "collapse" (intermédiaire)
collapse_template = """The following is a set of summaries:
{text}
Consolidate them into a clear and well-organized intermediate summary. {prompt_size}.{custom_prompt}
Respond ONLY with a valid JSON object matching this schema: {{"summary": "..."}}
Helpful Answer in {language}:"""


class MapOutput(BaseModel):
    """Output for the map and collapse steps."""

    summary: str = Field(description="The generated summary text")


class SummaryOutput(BaseModel):
    summary: str = Field(description="The generated summary text")


# Définition des PromptTemplates avec les variables d'entrée appropriées
MAP_PROMPT = PromptTemplate(template=map_template, input_variables=["text", "language"])

COMBINE_PROMPT = PromptTemplate(
    template=combine_template,
    input_variables=["text", "language", "prompt_size", "custom_prompt"],
)

COLLAPSE_PROMPT = PromptTemplate(
    template=collapse_template,
    input_variables=["text", "language", "prompt_size", "custom_prompt"],
)


class StuffSummarizeChain:
    """Reimplementation of the legacy `load_summarize_chain(chain_type="stuff")`
    removed in LangChain 1.x: stuffs every input document's content into the
    prompt's "text" variable and runs it through the LLM."""

    def __init__(
        self,
        llm: ChatOpenAI,
        prompt: PromptTemplate,
        output_schema: Type[Union[MapOutput, SummaryOutput]] = SummaryOutput,
    ):
        structured_llm = llm.with_structured_output(output_schema, method="json_mode")
        self._runnable = prompt | structured_llm

    async def ainvoke(self, inputs: dict, config: dict | None = None) -> dict:
        input_documents: list[Document] = inputs["input_documents"]
        chain_inputs = {
            **{key: value for key, value in inputs.items() if key != "input_documents"},
            "text": "\n\n".join(doc.page_content for doc in input_documents),
        }
        output: SummaryOutput = await self._runnable.ainvoke(chain_inputs, config=config or {})
        return {
            "input_documents": input_documents,
            "output_text": output.summary,
            "output": output,
        }


config = {}

if os.environ.get("LANGFUSE_PUBLIC_KEY"):
    try:
        Langfuse(
            public_key=os.environ.get("LANGFUSE_PUBLIC_KEY"),
            secret_key=os.environ.get("LANGFUSE_SECRET_KEY", ""),
            environment=os.environ.get("LANGFUSE_ENVIRONMENT", "local"),
            host=os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com"),
        )
        langfuse = get_client()
        if langfuse.auth_check():
            langfuse_handler = CallbackHandler()
            config["callbacks"] = [langfuse_handler]
    except Exception as e:
        logger_abrege.warning(f"Langfuse initialization skipped: {e}")


class TextResultNotGiven(Exception):
    """Exception raised when no text result is given."""


class LangChainAsyncMapReduceService(BaseSummaryService):
    def __init__(self, llm: ChatOpenAI, max_token: int = 128_000, max_concurrency: int = 5):
        super().__init__()
        self.llm = llm
        self.max_concurrency = max_concurrency
        self.llm_chain_map = StuffSummarizeChain(llm, MAP_PROMPT, output_schema=MapOutput)
        self.combine_document_chain = StuffSummarizeChain(llm, COMBINE_PROMPT, output_schema=SummaryOutput)
        self.collapse_document_chain = StuffSummarizeChain(llm, COLLAPSE_PROMPT, output_schema=MapOutput)
        if isinstance(max_token, str):
            max_token = int(max_token)
        self.max_token = max_token

    def split_task_texts(self, task: TaskModel) -> list[str]:
        """Split a task's source texts into chunks respecting the model's token limit.

        Shared between the normal summarize flow and the standalone re-trigger of
        Q&A/entity extraction, so both operate on the exact same chunk boundaries.
        """
        current_text = task.output.texts_found
        max_token = self.max_token
        if self.llm.max_tokens:
            max_token = min(self.max_token, self.llm.max_tokens)
        return split_texts_by_token_limit(texts=current_text, max_tokens=max_token)

    def dispatch_chunk_extraction(self, task_id: str, chunk_index: int, text: str, language: str, qa_per_chunk: int) -> None:
        """Fire-and-forget a Celery task extracting Q&A/entities/relationships for one chunk.

        Runs fully decoupled from the summarize flow (own Celery message, own worker slot)
        so it never adds latency to the summary itself.
        """
        page = extract_leading_page_number(text)
        celery_app.send_task(
            "worker.tasks.extract_chunk_details",
            args=[
                json.dumps(
                    {
                        "task_id": task_id,
                        "chunk_index": chunk_index,
                        "page": page,
                        "text": text,
                        "language": language,
                        "qa_per_chunk": qa_per_chunk,
                    }
                )
            ],
            task_id=f"{task_id}:chunk:{chunk_index}",
        )

    def dispatch_all_chunks(self, task_id: str, texts: list[str], language: str, qa_per_chunk: int) -> None:
        """Initialize the completion counter and dispatch one extraction task per chunk.

        The Redis counter (rather than a Celery chord) tracks when the last chunk finishes,
        since the Celery app here has no result backend configured for chord support.
        """
        redis_client.set(f"chunk_pending:{task_id}", len(texts))
        for index, text in enumerate(texts):
            self.dispatch_chunk_extraction(task_id=task_id, chunk_index=index, text=text, language=language, qa_per_chunk=qa_per_chunk)

    def dispatch_topic_classification(self, task_id: str, summary: str, language: str) -> None:
        """Fire-and-forget the free-form topic/subject classification of the final summary.

        Runs as its own Celery message once the summary is ready, so it never adds latency
        to `summarize()` — same rationale as `dispatch_chunk_extraction`.
        """
        celery_app.send_task(
            "worker.tasks.classify_topics",
            args=[json.dumps({"task_id": task_id, "summary": summary, "language": language})],
            task_id=f"{task_id}:topics",
        )

    async def map_documents(
        self,
        task: TaskModel,
        language: str,
        prompt_size: str = "",
        custom_prompt: str = "",
        extract_qa: bool = False,
        qa_per_chunk: int = 3,
    ) -> list[Document]:
        extra_log = {"task.id": task.id, "user_id": task.user_id}
        semaphore = asyncio.Semaphore(self.max_concurrency)
        lock = asyncio.Lock()
        counter = 0
        task = self.update_result_task(
            task=task,
            percentage=task.percentage,
            status=TaskStatus.IN_PROGRESS,
            result=task.output,
        )
        current_percentage = task.percentage
        if current_percentage is None:
            current_percentage = 0.0
        print_percentage = current_percentage * 100
        logger_abrege.debug(f"current percentage {print_percentage:.2f}%", extra=extra_log)
        if task.output is None or not task.output.texts_found:
            raise TextResultNotGiven("No text is given")

        transform_texts: list[str] = self.split_task_texts(task)
        nb_total_documents = len(transform_texts)
        logger_abrege.debug(
            f"After transformation, number of documents {nb_total_documents} - {[len(text.split()) for text in transform_texts]}",  # noqa
            extra=extra_log,
        )
        percentage_left = 1 - current_percentage

        if extract_qa and qa_per_chunk > 0:
            task_table.update_task(task_id=task.id, form_data=TaskUpdateForm(qa_entities_status="in_progress"))
            self.dispatch_all_chunks(task_id=task.id, texts=transform_texts, language=language, qa_per_chunk=qa_per_chunk)

        async def map_one_document(doc: Document) -> Document:
            nonlocal counter
            nonlocal task
            async with semaphore:
                try:
                    inputs = {
                        "input_documents": [doc],
                        "language": language,
                        "prompt_size": prompt_size,
                        "custom_prompt": custom_prompt,
                    }
                    t_doc_summary = perf_counter()
                    # TODO: add metadata to config to make sure to have more context
                    # config["metadata"] = {
                    #     "langfuse_user_id": "user123",
                    #     "langfuse_session_id": "sessionABC",
                    #     "langfuse_tags": ["test", "urgent"]
                    # }
                    tmp_copy_config = config.copy()
                    if tmp_copy_config:
                        tmp_copy_config["metadata"] = {
                            "langfuse_user_id": task.user_id,
                            "langfuse_session_id": task.id,
                            "langfuse_tags": ["map_one_document"],
                        }  # ty:ignore[invalid-assignment]

                    summary = await self.llm_chain_map.ainvoke(inputs, config=tmp_copy_config)
                    copy_log = extra_log.copy()
                    copy_log["process_name"] = "llm_chain_map.ainvoke"
                    copy_log["process_time"] = perf_counter() - t_doc_summary  # ty:ignore[invalid-assignment]
                    logger_abrege.info(f"{counter} / {nb_total_documents} processed", extra=copy_log)
                    async with lock:
                        counter += 1
                        percentage_map = counter / (nb_total_documents + 1)
                        percentage_map = percentage_left * percentage_map
                        logger_abrege.debug(
                            f"left percentage {100 * percentage_left:.2f}% {100 * current_percentage:.2f}% current_ma_percentage {100 * percentage_map:.2f}",
                            extra=extra_log,
                        )
                        task.percentage = current_percentage + percentage_map
                        new_summary: str = summary["output_text"]
                        partial_sum = Text(
                            id=hashlib.md5(new_summary.encode()).hexdigest(),
                            text=new_summary,
                            word_count=len(new_summary.split()),
                        )
                        if task.output is None or not task.output.partial_summaries:
                            task.output.partial_summaries = []

                        task.output.partial_summaries.append(partial_sum)

                        task = self.update_result_task(
                            task=task,
                            result=task.output,
                            percentage=task.percentage,
                            status=TaskStatus.IN_PROGRESS,
                        )

                    return Document(page_content=summary["output_text"], metadata=doc.metadata)
                except Exception as e:
                    logger_abrege.error(f"{e} - {traceback.format_exc()}", extra=extra_log)
                    raise e

        docs = [Document(page_content=text) for text in transform_texts]
        return await asyncio.gather(*[map_one_document(doc) for doc in docs])

    async def collapse_summary_chain(
        self,
        task: TaskModel,
        docs: list[Document],
        language: str,
        prompt_size: str = "",
        custom_prompt: str = "",
    ) -> list[Document]:
        extra_log = {"task.id": task.id}
        texts = [doc.page_content for doc in docs]
        total_words = sum_words(texts=texts)
        max_word = int(self.max_token * 0.75)
        logger_abrege.info(
            f"Collapse document because current total words {total_words} > {self.max_token}",
            extra=extra_log,
        )
        if total_words > max_word:
            semaphore = asyncio.Semaphore(self.max_concurrency)
            lock = asyncio.Lock()
            counter = 0
            current_percentage = task.percentage if task.percentage is not None else 0.0
            logger_abrege.debug(f"current percentage {current_percentage * 100:.2f}%", extra=extra_log)
            nb_total_documents = len(docs)
            partition_texts = group_by_max_word_sum(texts=texts, threshold=max_word)
            nb_total_documents = len(partition_texts)
            partition_documents: list[list[Document]] = []
            for texts in partition_texts:
                documents = []
                for text in texts:
                    documents.append(Document(page_content=text))

                partition_documents.append(documents)
            percentage_left = 1 - current_percentage

            async def collapse_summary_document(doc: list[Document]) -> Document:
                nonlocal counter
                nonlocal task
                async with semaphore:
                    try:
                        inputs = {
                            "input_documents": doc,
                            "language": language,
                            "prompt_size": prompt_size,
                            "custom_prompt": custom_prompt,
                        }
                        t_doc_summary = perf_counter()
                        tmp_copy_config = config.copy()
                        if tmp_copy_config:
                            tmp_copy_config["metadata"] = {
                                "langfuse_user_id": task.user_id,
                                "langfuse_session_id": task.id,
                                "langfuse_tags": ["collapse_summary_document"],
                            }  # ty:ignore[invalid-assignment]
                        summary = await self.collapse_document_chain.ainvoke(inputs, config=tmp_copy_config)
                        copy_log = extra_log.copy()
                        copy_log["process_name"] = "collapse_summary_chain.ainvoke"
                        copy_log["process_time"] = (
                            perf_counter() - t_doc_summary  # ty:ignore[invalid-assignment]
                        )  # ty:ignore[invalid-assignment]
                        logger_abrege.info(
                            f"{counter + 1} / {nb_total_documents} processed",
                            extra=copy_log,
                        )
                        async with lock:
                            counter += 1
                            percentage_map = counter / (nb_total_documents + 1)
                            percentage_map = current_percentage + percentage_left * percentage_map
                            logger_abrege.debug(
                                f"left percentage {100 * percentage_left:.2f}%| old percentage {100 * current_percentage:.2f}%"
                                f"current_ma_percentage {100 * percentage_map:.2f}",
                                extra=extra_log,
                            )
                            task.percentage = percentage_map
                            new_summary: str = summary["output_text"]
                            partial_sum = Text(
                                id=hashlib.md5(new_summary.encode()).hexdigest(),
                                text=new_summary,
                                word_count=len(new_summary.split()),
                            )
                            task.output.partial_summaries.append(partial_sum)
                            task = self.update_result_task(
                                task=task,
                                result=task.output,
                                percentage=task.percentage,
                                status=TaskStatus.IN_PROGRESS,
                            )

                        return Document(page_content=summary["output_text"])
                    except Exception as e:
                        logger_abrege.error(f"{e} - {traceback.format_exc()}", extra=extra_log)
                        raise e

            return await asyncio.gather(*[collapse_summary_document(doc) for doc in partition_documents])
        else:
            return docs

    async def acall(self, task: TaskModel) -> dict:
        params = task.parameters
        if not params:
            params = SummaryParameters()

        language = params.language if params.language else "French"
        prompt_size = (f"in at most {params.size} words" if params.size else "",)
        custom_prompt = params.custom_prompt if params.custom_prompt else ""

        mapped_docs: list[Document] = await self.map_documents(
            task=task,
            language=language,
            prompt_size=prompt_size,
            custom_prompt=custom_prompt,
            extract_qa=params.extract_qa,
            qa_per_chunk=params.qa_per_chunk,
        )
        texts = [doc.page_content for doc in mapped_docs]
        total_words = sum_words(texts=texts)
        max_word = int(self.max_token * 0.75)

        # TODO: WARNING maybe need more than 1 check :
        # while total_words > max_word:
        #     mapped_docs = await self.collapse_summary_chain(task=task, docs=mapped_docs, language=language, prompt_size=prompt_size, custom_prompt=custom_prompt)
        #     total_words = sum_words(texts=texts)

        if total_words > max_word:
            mapped_docs = await self.collapse_summary_chain(
                task=task,
                docs=mapped_docs,
                language=language,
                prompt_size=prompt_size,
                custom_prompt=custom_prompt,
            )

        combine_input = {
            "input_documents": mapped_docs,
            "language": language,
            "prompt_size": prompt_size,
            "custom_prompt": custom_prompt,
        }
        final_output = await self.combine_document_chain.ainvoke(combine_input)
        return final_output

    def summarize(self, task: TaskModel, *args, **kwargs) -> TaskModel:
        task.extras = task.extras or {}
        task.output = SummaryModel(
            created_at=task.output.created_at,
            updated_at=int(time.time()),
            summary="",
            word_count=0,
            percentage=task.percentage,
            model_name=self.llm.model_name,
            model_version=self.llm.model_name,
            status=TaskStatus.IN_PROGRESS.value,
            texts_found=task.output.texts_found,
            partial_summaries=[],
            qa_items=[],
            extras={},
        )

        logger_abrege.info(
            f"Début du processus de map-reduce avec {len(task.output.texts_found)} documents",
            extra={"task.id": task.id},
        )

        try:
            init_summary_perf = perf_counter()
            summary = asyncio.run(self.acall(task=task))
            logger_abrege.info(
                f"Summary generated in {perf_counter() - init_summary_perf:.2f} seconds",
                extra={"task.id": task.id},
            )

            task.output.percentage = 1
            task.status = TaskStatus.COMPLETED.value
            task.output.summary = summary["output_text"]
            task.output.word_count = len(task.output.summary.split())

            logger_abrege.info(
                f"{task.output.word_count} words",
                extra={"task.id": task.id, "user_id": task.user_id},
            )

            params = task.parameters or SummaryParameters()
            task_table.update_task(task_id=task.id, form_data=TaskUpdateForm(topics_status="pending"))
            self.dispatch_topic_classification(
                task_id=task.id,
                summary=task.output.summary,
                language=params.language if params.language else "French",
            )

            task = self.update_result_task(
                task,
                result=task.output,
                status=TaskStatus.COMPLETED,
                percentage=1,
            )
            return task
        except Exception as e:
            logger_abrege.error(
                f"Erreur lors du résumé : {e}",
                extra={"task.id": task.id, "user_id": task.user_id},
            )
            logger_abrege.error(
                traceback.format_exc(),
                extra={"task.id": task.id, "user_id": task.user_id},
            )
            task.status = TaskStatus.FAILED.value
            task.extras["error"] = str(e)  # ty:ignore[invalid-assignment]
            task = self.update_result_task(
                task,
                result=task.output,
                status=TaskStatus.FAILED,
                percentage=0,
            )

            return task
