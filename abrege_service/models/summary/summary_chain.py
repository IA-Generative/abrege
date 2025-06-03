import time
from time import perf_counter
import traceback

from langchain.chains.summarize import load_summarize_chain
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI

from src.schemas.result import SummaryModel
from src.schemas.task import TaskModel, TaskStatus
from src.utils.logger import logger_abrege

from abrege_service.models.base import BaseSummaryService
from langchain_core.prompts import PromptTemplate

# Prompt pour l'étape de "map"
map_template = """The following is a set of documents:
{text}
Based on this list of docs, summarize concisely.
Helpful Answer in {language}:"""

# Prompt pour l'étape de "reduce"
combine_template = """The following is a set of summaries:
{text}
Take these and distill it into a final, consolidated summary written of the main themes {size}.{custom_prompt}
Helpful Answer in {language}:"""

# Définition des PromptTemplates avec les variables d'entrée appropriées
MAP_PROMPT = PromptTemplate(template=map_template, input_variables=["text", "language"])

COMBINE_PROMPT = PromptTemplate(
    template=combine_template,
    input_variables=["text", "language", "size", "custom_prompt"],
)


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

        logger_abrege.info(
            f"Début du processus de map-reduce avec {len(task.output.texts_found)} documents",
            extra={"task.id": task.id},
        )

        documents = [Document(page_content=text) for text in task.output.texts_found]
        chain_perf_instantiate = perf_counter()
        chain = load_summarize_chain(
            self.llm,
            chain_type="map_reduce",
            verbose=True,
            map_prompt=MAP_PROMPT,
            combine_prompt=COMBINE_PROMPT,
        )
        logger_abrege.info(
            f"Chain instantiated in {perf_counter() - chain_perf_instantiate:.2f} seconds",
            extra={"task.id": task.id},
        )

        try:
            init_summary_perf = perf_counter()
            summary = chain.invoke(
                {
                    "input_documents": documents,
                    "language": params.language if params.language else "French",
                    "size": f"in at most {params.size} words" if params.size else "",
                    "custom_prompt": (params.custom_prompt if params.custom_prompt else ""),
                }
            )
            logger_abrege.info(
                f"Summary generated in {perf_counter() - init_summary_perf:.2f} seconds",
                extra={"task.id": task.id},
            )

            task.output.percentage = 1
            task.status = TaskStatus.COMPLETED.value
            task.output.summary = summary["output_text"]
            task.output.word_count = len(summary.split())
            logger_abrege.info(
                f"{task.output.word_count} words",
                extra={"task.id": task.id},
            )

            task = self.update_result_task(
                task,
                result=task.output,
                status=TaskStatus.COMPLETED.value,
                percentage=1,
            )
            return task
        except Exception as e:
            logger_abrege.error(
                f"Erreur lors du résumé : {e}",
                extra={"task.id": task.id},
            )
            logger_abrege.error(
                traceback.format_exc(),
                extra={"task.id": task.id},
            )
            task.status = TaskStatus.FAILED.value
            task.extras["error"] = str(e)
            task = self.update_result_task(
                task,
                result=task.output,
                status=TaskStatus.FAILED.value,
                percentage=0,
            )

            return task
