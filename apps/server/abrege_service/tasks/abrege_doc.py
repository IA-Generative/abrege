import os
from typing import List
import time
import json
import traceback

from abrege_service.utils.file import hash_file
from abrege_service.modules.base import BaseService


from abrege_service.config.openai import OpenAISettings

from src.models.task import TaskModel, TaskStatus, TaskUpdateForm, TaskName
from src.schemas.content import DocumentModel
from src.clients import celery_app, file_connector
from celery import Task
from src.utils.logger import logger_abrege
from src.services.merge_task_service import merge_task_service
from src.models.merge_task import MergeTaskUpdateForm
from .merge import launch_merge
from abrege_service.clients.server import ServerClient
from .chunk_task import launch_chunking
from .update_task import updating_task
from abrege_service.schemas import IMAGE_CONTENT_TYPES, PDF_CONTENT_TYPES
from .tools import (
    cache_service,
    audio_service,
    video_service,
    microsof_service,
    microsoft_service_older,
    libre_office_service,
    flat_text_service,
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
    libre_office_service,
]


class AbregeTask(Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger_abrege.error(f"Task {task_id} failed: {exc} - {traceback.format_exc()}")
        task = merge_task_service.get_by_related_task_id(task_id=task_id)
        if task:
            merge_task_service.update_merge_task(
                task_id=task.id,
                merge_task_update=MergeTaskUpdateForm(
                    status=TaskStatus.FAILED.value,
                ),
            )

    def on_success(self, retval, task_id, args, kwargs):
        logger_abrege.info(f"Task {task_id} completed successfully")
        current_task = server_client.get_task(task_id=task_id)
        launch_chunking.apply_async(
            args=[json.dumps(current_task)],
            task_id=f"{task_id}-chunking",
        )
        task = merge_task_service.get_by_related_task_id(task_id=task_id)
        if task:
            merge_task_service.update_merge_task(
                task_id=task.id,
                merge_task_update=MergeTaskUpdateForm(
                    status=TaskStatus.COMPLETED.value,
                    percentage=1,
                ),
            )
            task = merge_task_service.get_by_related_task_id(task_id=task_id)
            if task and merge_task_service.is_merge_completed(merge_id=task.merge_id):
                logger_abrege.info(f"All tasks for merge {task.merge_id} are completed. Marking merge as completed.")
                merge_task_model = server_client.get_task(task_id=task.merge_id)
                merge_task_model = TaskModel.model_validate(merge_task_model)
                if merge_task_model is None:
                    logger_abrege.error(f"Merge TaskModel {task.merge_id} not found")
                    return
                launch_merge.apply_async(
                    args=[json.dumps(merge_task_model.model_dump())],
                    task_id=task.merge_id,
                )


@celery_app.task(name=TaskName.ABREGE_DOCUMENT.value, bind=True, base=AbregeTask)
def process_non_pdf_images(self: AbregeTask, task: str):
    task: TaskModel = TaskModel.model_validate(json.loads(task))
    task.extras = task.extras or {}
    extra_log = {
        "user_id": task.user_id,
        "task_id": task.id,
        "action": TaskName.ABREGE_DOCUMENT.value,
    }
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

            if isinstance(task.input, DocumentModel):
                logger_abrege.debug(f"Processing Document task: {task.id}")
                file_path = file_connector.get_by_task_id(user_id=task.user_id, task_id=task.id)
                task.input.file_path = file_path
                task.content_hash = hash_file(file_path)
                if task.input.content_type in IMAGE_CONTENT_TYPES + PDF_CONTENT_TYPES:
                    raise NotImplementedError(f"Content type {task.input.content_type} should be processed in abrege_pdf_image task")
                for service in services:
                    if service.is_available(task):
                        logger_abrege.info(f"Using service: {service.__class__.__name__}")
                        task = service.process_task(task=task)
                        break

                if os.path.exists(file_path):
                    os.remove(file_path)

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
