import os
from typing import List
import time
import json

import openai
from langchain_openai import ChatOpenAI

from abrege_service.modules.base import BaseService
from abrege_service.modules.url import URLService
from abrege_service.modules.audio import AudioVoskTranscriptionService
from abrege_service.modules.ocr import OCRMIService
from abrege_service.modules.video import VideoTranscriptionService
from abrege_service.modules.doc import (
    MicrosoftDocumnentToMdService,
    FlatTextService,
    # PDFTOMD4LLMService,
)

from abrege_service.models.summary.parallele_summary_chain import LangChainAsyncMapReduceService
from abrege_service.config.openai import OpenAISettings

from src.schemas.task import TaskModel, task_table, TaskStatus, TaskUpdateForm
from src.schemas.content import URLModel, DocumentModel, TextModel
from src.schemas.result import ResultModel
from src.clients import celery_app, file_connector
from src import __version__


audio_service = AudioVoskTranscriptionService()
video_service = VideoTranscriptionService()
microsof_service = MicrosoftDocumnentToMdService()
flat_text_service = FlatTextService()
# pdf_service = PDFTOMD4LLMService()
ocr_service = OCRMIService()
services: List[BaseService] = [
    audio_service,
    video_service,
    microsof_service,
    flat_text_service,
    ocr_service,
]
url_service = URLService(services=services)


openai_settings = OpenAISettings()
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
    llm=llm, max_token=os.getenv("MAX_MODEL_TOKEN", 128_000), max_concurrency=int(os.getenv("MAX_CONCURRENCY_LLM_CALL", 5))
)
tmp_folder = os.environ.get("CACHE_FOLDER")
os.makedirs(tmp_folder, exist_ok=True)


@celery_app.task(name="worker.tasks.abrege", bind=True)
def launch(self, task: str):
    task: TaskModel = TaskModel.model_validate(json.loads(task))
    task.extras = task.extras or {}
    try:
        task_table.update_task(
            task_id=task.id,
            form_data=TaskUpdateForm(
                status=TaskStatus.IN_PROGRESS.value,
                updated_at=int(time.time()),
            ),
        )

        if isinstance(task.input, URLModel):
            task = url_service.process_task(task=task)

        elif isinstance(task.input, DocumentModel):
            file_path = file_connector.get_by_task_id(user_id=task.user_id, task_id=task.id)
            task.input.file_path = file_path
            for service in services:
                if service.is_availble(task.input.content_type):
                    task = service.process_task(task=task)

            if os.path.exists(file_path):
                os.remove(file_path)

        elif isinstance(task.input, TextModel):
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

        task = summary_service.process_task(task=task)
        return task.model_dump()

    except Exception as e:
        task_table.update_task(
            task_id=task.id,
            form_data=TaskUpdateForm(
                status=TaskStatus.FAILED.value,
                updated_at=int(time.time()),
                extras={"error": f"{e}"},
            ),
        )
        raise e
