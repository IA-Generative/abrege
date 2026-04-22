import os
from typing import List
import time
import json
import traceback

import openai
from langchain_openai import ChatOpenAI
from abrege_service.utils.file import hash_file, hash_string
from abrege_service.modules.base import BaseService
from abrege_service.modules.url import URLService
from abrege_service.modules.audio import AudioVoskTranscriptionService
from abrege_service.modules.video import VideoTranscriptionService
from abrege_service.modules.documents.openoffice import LibreOfficeDocumentToMdService
from abrege_service.modules.doc import (
    MicrosoftDocumnentToMdService,
    FlatTextService,
    MicrosoftOlderDocumentToMdService,
    # PDFTOMD4LLMService,
)
from abrege_service.modules.image import ImageFromVLM
from abrege_service.modules.ocr import OCRMIService
from abrege_service.modules.cache import CacheService

from abrege_service.models.summary.parallele_summary_chain import (
    LangChainAsyncMapReduceService,
)
from abrege_service.config.openai import OpenAISettings

from src.models.task import TaskModel, TaskStatus, TaskUpdateForm, TaskName
from src.schemas.content import URLModel, DocumentModel, TextModel
from src.schemas.result import ResultModel
from src.clients import celery_app, file_connector
from celery import Task
from src import __version__
from src.utils.logger import logger_abrege
from src.services.merge_task_service import merge_task_service
from src.models.merge_task import MergeTaskUpdateForm
from .merge import launch_merge
from abrege_service.clients.server import ServerClient
from .chunk_task import launch_chunking

openai_settings = OpenAISettings()
server_client = ServerClient()
cache_service = CacheService()
audio_service = AudioVoskTranscriptionService(service_ratio_representaion=0.5)
video_service = VideoTranscriptionService(service_ratio_representaion=0.5)
microsof_service = MicrosoftDocumnentToMdService()
microsoft_service_older = MicrosoftOlderDocumentToMdService()
libre_office_service = LibreOfficeDocumentToMdService()
flat_text_service = FlatTextService()

if os.environ.get("OCR_SERVICE_LLM") == "LLM":
    ocr_service = ImageFromVLM()
else:
    ocr_service = OCRMIService(url_ocr=os.environ.get("OCR_BACKEND_URL"))
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
url_service = URLService(services=services)


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
tmp_folder = os.environ.get("CACHE_FOLDER")
os.makedirs(tmp_folder, exist_ok=True)


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


@celery_app.task(name=TaskName.ABREGE.value, bind=True, base=AbregeTask)
def launch(self: AbregeTask, task: str):
    task: TaskModel = TaskModel.model_validate(json.loads(task))
    task.extras = task.extras or {}
    extra_log = {"user_id": task.user_id, "task_id": task.id, "action": "launch"}
    with logger_abrege.contextualize(**extra_log):  # ty:ignore[unresolved-attribute]
        try:
            server_client.update_task(
                task_id=task.id,
                data=TaskUpdateForm(
                    status=TaskStatus.IN_PROGRESS.value,
                    updated_at=int(time.time()),
                ).model_dump(exclude_none=True),
            )
            logger_abrege.info("Task started processing")
            logger_abrege.info(f"Task input: {task.input}")
            t = time.time()
            if isinstance(task.input, URLModel):
                logger_abrege.debug(f"Processing URL task: {task.id}")
                task = url_service.process_task(task=task)

            elif isinstance(task.input, DocumentModel):
                logger_abrege.debug(f"Processing Document task: {task.id}")
                file_path = file_connector.get_by_task_id(user_id=task.user_id, task_id=task.id)
                task.input.file_path = file_path
                task.content_hash = hash_file(file_path)
                for service in services:
                    if service.is_available(task):
                        logger_abrege.info(f"Using service: {service.__class__.__name__}")
                        task = service.process_task(task=task)
                        break

                if os.path.exists(file_path):
                    os.remove(file_path)

            elif isinstance(task.input, TextModel):
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
                raise NotImplementedError("Content type not supported")
            if task.output is None:
                raise ValueError("Task output is None after processing")

            logger_abrege.debug(f"Task processed in {time.time() - t} seconds")

            t = time.time()
            task = summary_service.process_task(task=task)
            logger_abrege.info(
                f"Summary Task {task.id} processed in {time.time() - t} seconds",
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
