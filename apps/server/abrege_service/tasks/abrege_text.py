import os
import time
import json
import traceback

import openai
from langchain_openai import ChatOpenAI
from abrege_service.utils.file import hash_string

from abrege_service.models.summary.parallele_summary_chain import (
    LangChainAsyncMapReduceService,
)
from abrege_service.config.openai import OpenAISettings

from src.models.task import TaskModel, TaskStatus, TaskUpdateForm, TaskName
from src.schemas.content import TextModel
from src.schemas.result import ResultModel
from src.clients import celery_app
from celery import Task
from src import __version__
from src.utils.logger import logger_abrege
from src.services.merge_task_service import merge_task_service
from src.models.merge_task import MergeTaskUpdateForm
from .merge import launch_merge
from abrege_service.clients.server import ServerClient
from .chunk_task import launch_chunking
from .update_task import updating_task

openai_settings = OpenAISettings()
server_client = ServerClient()


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

                launch_merge.apply_async(
                    args=[json.dumps(merge_task_model.model_dump())],
                    task_id=task.merge_id,
                )


@celery_app.task(name=TaskName.ABREGE_TEXT.value, bind=True, base=AbregeTask)
def text_summary_process(self: AbregeTask, task: str) -> dict:
    task: TaskModel = TaskModel.model_validate(json.loads(task))
    task.extras = task.extras or {}
    extra_log = {
        "user_id": task.user_id,
        "task_id": task.id,
        "action": TaskName.ABREGE_TEXT.value,
        "current_task_id": task.id,
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

            if isinstance(task.input, TextModel):
                logger_abrege.debug(f"Processing Text task: {task.id}")
                task.content_hash = hash_string(task.input.text)
                task.output = ResultModel(
                    type="flat",
                    created_at=task.input.created_at,
                    model_name="flat",
                    model_version=__version__,
                    percentage=1,
                    texts_found=[task.input.text],
                )
            else:
                raise NotImplementedError(f"Content type {type(task.input).__name__} not supported in text_summary task")

            logger_abrege.debug(f"Task processed in {time.time() - t} seconds")

            t = time.time()
            task = summary_service.process_task(task=task)
            logger_abrege.info(
                f"Summary Task {task.id} processed in {time.time() - t} seconds",
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
