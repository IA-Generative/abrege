import os
import time
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


from src.schemas.result import SummaryModel, Text, EntityModel, RelationshipModel, QAItem
from src.schemas.parameters import SummaryParameters
from src.schemas.task import TaskModel, TaskStatus
from src.utils.logger import logger_abrege


from abrege_service.models.base import BaseSummaryService
from abrege_service.models.summary.qa_chain import build_qa_runnable, extract_leading_page_number
from abrege_service.utils.text import (
    split_texts_by_token_limit,
    split_texts_by_word_limit,
    sum_words,
    group_by_max_word_sum,
)

# Prompt pour l'étape de "map"
map_template = """The following is a set of documents:
{text}
Based on this list of docs:
1. Summarize concisely and clearly in paragraph form. Highlight the main ideas and recurring themes.
2. Extract the most important named entities (max 10): people, dates, organizations, locations, amounts. For each, provide only type and text.
Respond ONLY with a valid JSON object matching this schema: {{"summary": "...", "entities": [{{"type": "<the category you deem most appropriate, e.g. PERSON, DATE, ORGANIZATION, LOCATION, AMOUNT, EVENT, or any other relevant category>", "text": "..."}}]}}
Helpful Answer in {language}:"""

# Prompt pour l'étape de "reduce"
combine_template = """The following is a set of summaries:
{text}
Take these and:
1. Consolidate them into a clear and well-organized final summary. Highlight recurring ideas, themes, and insights. {prompt_size}.{custom_prompt}
2. Collect all named entities. For entities referring to the same real-world object, group them into a single entry and merge their pages and contexts — do NOT drop any occurrence.
3. Based on the entities and their contexts, infer relationships between pairs of entities (0-based indices). Only include relationships clearly supported by the text.
Respond ONLY with a valid JSON object matching this schema: {{"summary": "...", "entities": [{{"type": "<the category you deem most appropriate, e.g. PERSON, DATE, ORGANIZATION, LOCATION, AMOUNT, EVENT, or any other relevant category>", "text": "...", "contexts": ["..."], "pages": [1]}}], "relationships": [{{"source_index": 0, "target_index": 1, "relationship_type": "...", "description": "..."}}]}}
Helpful Answer in {language}:"""

# Prompt pour l'étape de "collapse" (intermédiaire) — sans relations
collapse_template = """The following is a set of summaries:
{text}
Take these and:
1. Consolidate them into a clear and well-organized intermediate summary. {prompt_size}.{custom_prompt}
2. Extract the most important named entities (max 10): people, dates, organizations, locations, amounts.
Respond ONLY with a valid JSON object matching this schema: {{"summary": "...", "entities": [{{"type": "<the category you deem most appropriate, e.g. PERSON, DATE, ORGANIZATION, LOCATION, AMOUNT, EVENT, or any other relevant category>", "text": "..."}}]}}
Helpful Answer in {language}:"""


class EntityOutput(BaseModel):
    type: str = Field(
        description="The category of the entity, freely chosen to best describe it (e.g. PERSON, DATE, ORGANIZATION, LOCATION, AMOUNT, EVENT, or any other relevant category)"
    )
    text: str = Field(description="The normalized text value of the entity (e.g. full name, ISO date, etc.)")
    contexts: list[str] = Field(
        description="All sentences or phrases where this entity was found (one entry per occurrence, preserving duplicates across chunks)",
        default_factory=list,
    )
    pages: list[int] = Field(
        description="The list of page numbers where the entity was found",
        default_factory=list,
    )


class RelationshipOutput(BaseModel):
    source_index: int = Field(description="0-based index of the source entity in the entities list")
    target_index: int = Field(description="0-based index of the target entity in the entities list")
    relationship_type: str = Field(description="Type of relationship between the two entities")
    description: str = Field(description="Description of the relationship, including context and any relevant details")


class MapEntityOutput(BaseModel):
    """Minimal entity for the map step \u2014 no contexts or pages to keep output short."""

    type: str = Field(
        description="The category of the entity, freely chosen to best describe it (e.g. PERSON, DATE, ORGANIZATION, LOCATION, AMOUNT, EVENT, or any other relevant category)"
    )
    text: str = Field(description="The normalized text value of the entity (e.g. full name, ISO date)")


class MapOutput(BaseModel):
    """Lightweight output for the map and collapse steps \u2014 no relationships."""

    summary: str = Field(description="The generated summary text")
    entities: list[MapEntityOutput] = Field(
        description="A list of entities extracted from the text chunk",
        default_factory=list,
    )


class SummaryOutput(BaseModel):
    summary: str = Field(description="The generated summary text")
    entities: list[EntityOutput] = Field(
        description="A list of entities extracted from the summary",
        default_factory=list,
    )
    relationships: list[RelationshipOutput] = Field(
        description="A list of relationships between entities, inferred from their contexts. Only populated in the final reduce step.",
        default_factory=list,
    )


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
        self.qa_runnable = build_qa_runnable(llm)
        if isinstance(max_token, str):
            max_token = int(max_token)
        self.max_token = max_token

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

        current_text = task.output.texts_found
        nb_total_documents = len(current_text)
        max_token = self.max_token
        if self.llm.max_tokens:
            max_token = min(self.max_token, self.llm.max_tokens)

        logger_abrege.debug(f"max_token {max_token} - {type(max_token)}")
        logger_abrege.debug(
            f"Current number of documents {nb_total_documents}%",
            extra=extra_log,
        )
        try:
            transform_texts: list[str] = split_texts_by_token_limit(texts=current_text, max_tokens=max_token, model=self.llm.model_name)

        except Exception as e:
            logger_abrege.warning(f"{self.llm.model_name} - {e}")
            transform_texts: list[str] = split_texts_by_word_limit(current_text, max_words=int(max_token * 0.75))
        nb_total_documents = len(transform_texts)
        logger_abrege.debug(
            f"After transformation, number of documents {nb_total_documents} - max_words {int(max_token * 0.75)} - {[len(text.split()) for text in transform_texts]}",  # noqa
            extra=extra_log,
        )
        percentage_left = 1 - current_percentage

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

                    if extract_qa and qa_per_chunk > 0:
                        qa_config = config.copy()
                        if qa_config:
                            qa_config["metadata"] = {
                                "langfuse_user_id": task.user_id,
                                "langfuse_session_id": task.id,
                                "langfuse_tags": ["map_one_document_qa"],
                            }  # ty:ignore[invalid-assignment]
                        summary, qa_output = await asyncio.gather(
                            self.llm_chain_map.ainvoke(inputs, config=tmp_copy_config),
                            self.qa_runnable.ainvoke(
                                {
                                    "text": doc.page_content,
                                    "language": language,
                                    "qa_per_chunk": qa_per_chunk,
                                },
                                config=qa_config,
                            ),
                        )
                    else:
                        summary = await self.llm_chain_map.ainvoke(inputs, config=tmp_copy_config)
                        qa_output = None
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

                        if qa_output is not None and qa_output.items:
                            page = extract_leading_page_number(doc.page_content)
                            if task.output.qa_items is None:
                                task.output.qa_items = []
                            task.output.qa_items.extend(
                                QAItem(
                                    page=page,
                                    source_text=doc.page_content,
                                    question=item.question,
                                    answer=item.answer,
                                )
                                for item in qa_output.items
                            )

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

            final: SummaryOutput = summary.get("output")
            if final and hasattr(final, "entities"):
                task.output.entities = [
                    EntityModel(
                        type=e.type,
                        text=e.text,
                        contexts=e.contexts,
                        pages=e.pages,
                    )
                    for e in final.entities
                ]
                task.output.relationships = [
                    RelationshipModel(
                        source_index=r.source_index,
                        target_index=r.target_index,
                        relationship_type=r.relationship_type,
                        description=r.description,
                    )
                    for r in final.relationships
                ]
            logger_abrege.info(
                f"{task.output.word_count} words",
                extra={"task.id": task.id, "user_id": task.user_id},
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
