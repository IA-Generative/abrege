from typing import List
import time
import json
import traceback

from abrege_service.modules.base import BaseService


from abrege_service.config.openai import OpenAISettings

from src.models.task import TaskModel, TaskStatus, TaskUpdateForm, TaskName
from src.schemas.content import URLModel
from src.clients import celery_app
from src.utils.logger import logger_abrege
from abrege_service.clients.server import ServerClient
from .update_task import updating_task
from .base_task import AbregeTask
from .tools import (
    cache_service,
    audio_service,
    video_service,
    microsof_service,
    microsoft_service_older,
    libre_office_service,
    flat_text_service,
    ocr_service,
    url_service,
    summary_service,
)

openai_settings = OpenAISettings()
server_client = ServerClient()

services: List[BaseService] = [
    cache_service,
    audio_service,
    video_service,
    microsoft_service_older,
    microsof_service,
    flat_text_service,
    ocr_service,
    libre_office_service,
]


@celery_app.task(name=TaskName.ABREGE_URL.value, bind=True, base=AbregeTask)
def process_url(self: AbregeTask, task: str):
    task: TaskModel = TaskModel.model_validate(json.loads(task))
    task.extras = task.extras or {}
    extra_log = {"user_id": task.user_id, "task_id": task.id, "action": "launch"}
    with logger_abrege.contextualize(**extra_log):  # ty:ignore[unresolved-attribute]
        try:
            updating_task.apply_async(
                args=[
                    task.id,
                    TaskUpdateForm(status=TaskStatus.IN_PROGRESS.value).model_dump(exclude_none=True),
                ],
                task_id=f"{task.id}-update-in-progress",
            )
            logger_abrege.info("Task started processing")
            logger_abrege.info(f"Task input: {task.input}")
            t = time.time()
            if isinstance(task.input, URLModel):
                logger_abrege.debug(f"Processing URL task: {task.id}")
                task = url_service.process_task(task=task)

            else:
                raise NotImplementedError("Content type not supported")
            if task.output is None:
                raise ValueError("Task output is None after processing")

            logger_abrege.debug(f"Task processed in {time.time() - t} seconds")

            t = time.time()
            task = summary_service.process_task(task=task)
            logger_abrege.info(
                f"Summary Task {task.id} processed in {time.time() - t} seconds",
            )
            updating_task.apply_async(
                args=[
                    task.id,
                    TaskUpdateForm(status=TaskStatus.COMPLETED.value, percentage=1).model_dump(exclude_none=True),
                ],
                task_id=f"{task.id}-update-completed",
            )
            return task.model_dump()

        except Exception as e:
            updating_task.apply_async(
                args=[
                    task.id,
                    TaskUpdateForm(
                        status=TaskStatus.FAILED.value,
                        updated_at=int(time.time()),
                        extras={"error": f"{e} - {traceback.format_exc()}"},
                    ).model_dump(exclude_none=True),
                ],
                task_id=f"{task.id}-update-failed",
            )
            logger_abrege.error(f"Task {task.id} failed: {e} - {traceback.format_exc()}")
            raise e
