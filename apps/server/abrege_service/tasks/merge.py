import os

import time
import json
import traceback

import openai
from langchain_openai import ChatOpenAI

from abrege_service.modules.cache import CacheService

from abrege_service.models.summary.parallele_summary_chain import (
    LangChainAsyncMapReduceService,
)
from abrege_service.config.openai import OpenAISettings

from src.schemas.task import TaskModel, task_table, TaskStatus, TaskUpdateForm, TaskName
from src.schemas.content import MergeModel
from src.schemas.result import ResultModel, SummaryModel
from src.clients import celery_app
from src import __version__
from src.utils.logger import logger_abrege

openai_settings = OpenAISettings()
cache_service = CacheService()


async_client = openai.AsyncOpenAI(
    api_key=openai_settings.OPENAI_API_KEY,
    base_url=openai_settings.OPENAI_API_BASE,
)

client = openai.OpenAI(
    api_key=openai_settings.OPENAI_API_KEY,
    base_url=openai_settings.OPENAI_API_BASE,
)


llm = ChatOpenAI(
    model=openai_settings.OPENAI_API_MODEL,
    temperature=0.0,
    api_key=openai_settings.OPENAI_API_KEY,
    base_url=openai_settings.OPENAI_API_BASE,
)
summary_service = LangChainAsyncMapReduceService(
    llm=llm,
    max_token=int(os.getenv("MAX_MODEL_TOKEN", 128_000)),
    max_concurrency=int(os.getenv("MAX_CONCURRENCY_LLM_CALL", 5)),
)


@celery_app.task(name=TaskName.MERGE.value)
def launch_merge(task: str) -> dict:
    task: TaskModel = TaskModel.model_validate(json.loads(task))
    task.extras = task.extras or {}
    extra_log = {"user_id": task.user_id, "task_id": task.id, "action": "launch_merge"}

    try:
        if task.input is None or not isinstance(task.input, MergeModel):
            logger_abrege.error(f"Task {task.id} has invalid input for merge", extra=extra_log)
            raise ValueError("Invalid input for merge task")

        input_task_ids = task.input.task_ids
        if not input_task_ids:
            logger_abrege.error(f"Task {task.id} has empty task_ids for merge", extra=extra_log)
            raise ValueError("No task ids provided for merge")
        if task.status in [
            TaskStatus.COMPLETED.value,
            TaskStatus.FAILED.value,
            TaskStatus.FAILED.value,
            TaskStatus.TIMEOUT.value,
        ]:
            logger_abrege.error(
                f"Task {task.id} has invalid status {task.status} for merge",
                extra=extra_log,
            )
            return task.model_dump()  # Avoid re-processing if already in progress or completed

        # Fetch the tasks to merge
        tasks_to_merge: list[str] = []
        progress: float = 0
        for task_id in input_task_ids:
            t = task_table.get_task_by_id(task_id)
            if t is None:
                logger_abrege.warning(
                    f"Task {task.id} references non-existent task id {task_id}",
                    extra=extra_log,
                )
                raise ValueError(f"Referenced task id {task_id} does not exist")
            else:
                if t.status != TaskStatus.COMPLETED.value:
                    logger_abrege.warning(
                        f"Task {task.id} references task id {task_id} with status {t.status}",
                        extra=extra_log,
                    )
                    current_progess = t.percentage if t.percentage else 0
                    progress += current_progess
                    if isinstance(t.output, SummaryModel):
                        tasks_to_merge.append(t.output.summary)

        output = ResultModel(
            type="merge",
            created_at=int(time.time()),
            model_name="merge",
            model_version=__version__,
            percentage=progress / len(input_task_ids),
            summaries_found=tasks_to_merge,
            texts_found=tasks_to_merge,
        )
        if len(tasks_to_merge) != len(input_task_ids):
            logger_abrege.error(f"Task {task.id} has no completed tasks to merge", extra=extra_log)

            task_found = task_table.update_task(
                task_id=task.id,
                form_data=TaskUpdateForm(
                    status=TaskStatus.IN_PROGRESS.value,
                    updated_at=int(time.time()),
                    percentage=progress / len(input_task_ids),
                    output=output,
                ),
            )
            if not task_found:
                raise ValueError(f"Failed to update task {task.id} with merge progress")
            return task_found.model_dump()

        t = time.time()

        logger_abrege.debug(f"Task processed in {time.time() - t} seconds", extra=extra_log)
        task = summary_service.process_task(task=task)
        t = time.time()
        logger_abrege.info(
            f"Summary Task {task.id} processed in {time.time() - t} seconds",
            extra=extra_log,
        )
        task_table.update_task(
            task_id=task.id,
            form_data=TaskUpdateForm(
                status=TaskStatus.COMPLETED.value,
                updated_at=int(time.time()),
                percentage=1,
                output=output,
            ),
        )
        return task.model_dump()

    except Exception as e:
        task_table.update_task(
            task_id=task.id,
            form_data=TaskUpdateForm(
                status=TaskStatus.FAILED.value,
                updated_at=int(time.time()),
                extras={"error": f"{e} - {traceback.format_exc()}"},
            ),
        )
        logger_abrege.error(f"Task {task.id} failed: {e} - {traceback.format_exc()}")
        raise e
