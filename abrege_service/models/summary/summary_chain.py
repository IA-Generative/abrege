import time
from time import perf_counter
import traceback

from langchain.chains.summarize import load_summarize_chain
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from src.schemas.result import SummaryModel
from src.schemas.task import TaskModel, TaskStatus
from src.utils.logger import logger_abrege

from abrege_service.models.base import BaseSummaryService


class LangChainMapReduceService(BaseSummaryService):
    def __init__(self, llm: ChatOpenAI):
        super().__init__()
        self.llm = llm

    def summarize(self, task: TaskModel, *args, **kwargs) -> TaskModel:
        task.extras = task.extras or {}
        task.output = SummaryModel(
            created_at=task.output.created_at,
            updated_at=int(time.time()),
            summary="",
            word_count=0,
            percentage=0,
            model_name=self.llm.model_name,
            model_version=self.llm.model_name,
            status=TaskStatus.IN_PROGRESS.value,
            texts_found=task.output.texts_found,
            extras={},
        )

        params = task.parameters
        size_final_summary_word = params.size or 4000  # Default to 4000 words if not specified

        logger_abrege.info(f"Début du processus de map-reduce avec {len(task.output.texts_found)} documents")

        documents = [Document(page_content=text) for text in task.output.texts_found]
        chain_perf_instantiate = perf_counter()
        chain = load_summarize_chain(
            self.llm,
            chain_type=params.method or "map_reduce",
            verbose=True,
            token_max=int(
                size_final_summary_word * 1.25
            ),  # 1.25 * nb_words give final summary size in tokens (approx. 1.25 tokens per word on average)
        )
        logger_abrege.info(f"Chain instantiated in {perf_counter() - chain_perf_instantiate:.2f} seconds")

        try:
            init_summary_perf = perf_counter()
            summary = chain.run(documents)
            logger_abrege.info(f"Summary generated in {perf_counter() - init_summary_perf:.2f} seconds")

            if params.custom_prompt:
                logger_abrege.info("Applying custom prompt to the summary")
                logger_abrege.debug(f"Custom prompt: {params.custom_prompt}")
                prompt = ChatPromptTemplate.from_messages(
                    [
                        ("system", params.custom_prompt),
                        ("human", "{text}"),
                    ]
                )
                formatted_prompt = prompt.format_prompt(text=summary)
                messages = formatted_prompt.to_messages()
                response = self.llm.invoke(messages)
                summary = response.content
                logger_abrege.info(f"Time final summary time: {perf_counter() - init_summary_perf:.2f} seconds")
            ############################################
            language = params.language if params.language is not None else "French"
            try:
                # TODO: use load_summarize_chain to use refine_prompt, for using custom_prompt and language
                response = self.llm.invoke(f"Translate to {language}: {summary}")
                summary = response.content
            except Exception as e:
                logger_abrege.error(f"{e}")
            ############################################

            task.output.percentage = 1
            task.status = TaskStatus.COMPLETED.value
            task.output.summary = summary
            task.output.word_count = len(summary.split())
            logger_abrege.info(f"{task.id} : {task.output.word_count} words")

            task = self.update_result_task(
                task,
                result=task.output,
                status=TaskStatus.COMPLETED.value,
                percentage=1,
            )
            return task
        except Exception as e:
            logger_abrege.error(f"Erreur lors du résumé : {e}")
            logger_abrege.error(traceback.format_exc())
            task.status = TaskStatus.FAILED.value
            task.extras["error"] = str(e)
            task = self.update_result_task(
                task,
                result=task.output,
                status=TaskStatus.FAILED.value,
                percentage=0,
            )

            return task
