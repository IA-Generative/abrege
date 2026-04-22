import os

import time
import json
import traceback


from abrege_service.modules.cache import CacheService

from abrege_service.models.summary.parallele_summary_chain import (
    LangChainAsyncMapReduceService,
)

from src.models.task import TaskModel, TaskStatus, TaskUpdateForm, TaskName
from src.schemas.content import MergeModel
from src.schemas.result import ResultModel, SummaryModel
from src.clients import celery_app
from src import __version__
from src.utils.logger import logger_abrege
from abrege_service.clients.server import ServerClient


server_client = ServerClient()


cache_service = CacheService()


summary_service = LangChainAsyncMapReduceService(
    max_token=int(os.getenv("MAX_MODEL_TOKEN", 128_000)),
    max_concurrency=int(os.getenv("MAX_CONCURRENCY_LLM_CALL", 5)),
)


@celery_app.task(name=TaskName.MERGE.value)
def launch_merge(task: str) -> dict:
    task: TaskModel = TaskModel.model_validate(json.loads(task))
    task.extras = task.extras or {}

    with logger_abrege.contextualize(  # ty:ignore[unresolved-attribute]
        task_id=task.id, user_id=task.user_id, action="merge"
    ):
        try:
            if task.input is None or not isinstance(task.input, MergeModel):
                logger_abrege.error(
                    f"Task {task.id} has invalid input for merge",
                )
                raise ValueError("Invalid input for merge task")

            input_task_ids = task.input.task_ids
            if not input_task_ids:
                logger_abrege.error(
                    f"Task {task.id} has empty task_ids for merge",
                )
                raise ValueError("No task ids provided for merge")
            if task.status in [
                TaskStatus.COMPLETED.value,
                TaskStatus.FAILED.value,
                TaskStatus.FAILED.value,
                TaskStatus.TIMEOUT.value,
            ]:
                logger_abrege.error(
                    f"Task {task.id} has invalid status {task.status} for merge",
                )
                return task.model_dump()  # Avoid re-processing if already in progress or completed

            # Fetch the tasks to merge
            tasks_to_merge: list[str] = []
            progress: float = 0
            for task_id in input_task_ids:
                t = server_client.get_task(task_id=task_id)
                t = TaskModel.model_validate(t)

                if t.status != TaskStatus.COMPLETED.value:
                    logger_abrege.warning(
                        f"Task {task.id} references task id {task_id} with status {t.status}",
                    )
                    current_progess = t.percentage if t.percentage else 0
                    progress += current_progess
                else:
                    logger_abrege.debug(
                        f"Task {t.output} references completed task id {task_id}",
                    )
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
            task.output = output
            server_client.update_task(
                task_id=task.id,
                data=TaskUpdateForm(
                    status=TaskStatus.IN_PROGRESS.value,
                    updated_at=int(time.time()),
                    percentage=task.output.percentage,
                    output=task.output,
                ).model_dump(exclude_none=True),
            )
            logger_abrege.info(
                tasks_to_merge,
            )
            logger_abrege.debug(
                f"Task {task.id} merge progress: {progress} / {len(input_task_ids)}",
            )
            if len(tasks_to_merge) != len(input_task_ids):
                raise ValueError(f"Not all tasks are completed for merge. Progress: {progress} / {len(input_task_ids)}")

            t = time.time()

            logger_abrege.debug(
                f"Task processed in {time.time() - t} seconds",
            )
            task = summary_service.process_task(task=task)
            t = time.time()
            logger_abrege.info(
                f"Summary Task {task.id} processed in {time.time() - t} seconds",
            )
            server_client.update_task(
                task_id=task.id,
                data=TaskUpdateForm(
                    status=TaskStatus.COMPLETED.value,
                    updated_at=int(time.time()),
                    percentage=1,
                    output=task.output,
                ).model_dump(exclude_none=True),
            )
            return task.model_dump()

        except Exception as e:
            server_client.update_task(
                task_id=task.id,
                data=TaskUpdateForm(
                    status=TaskStatus.FAILED.value,
                    updated_at=int(time.time()),
                    extras={"error": f"{e} - {traceback.format_exc()}"},
                ).model_dump(exclude_none=True),
            )
            logger_abrege.error(f"Task {task.id} failed: {e} - {traceback.format_exc()}")
            raise e
