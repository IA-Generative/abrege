import os
from typing import List
import time
import json

import openai

from abrege_service.modules.base import BaseService
from abrege_service.modules.url import URLService
from abrege_service.modules.audio import AudioVoskTranscriptionService
from abrege_service.modules.video import VideoTranscriptionService
from abrege_service.modules.doc import (
    MicrosoftDocumnentToMdService,
    FlatTextService,
    PDFTOMD4LLMService,
)

from abrege_service.models.summary.naive import NaiveSummaryService
from abrege_service.utils.text import split_texts_by_word_limit
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
pdf_service = PDFTOMD4LLMService()
services: List[BaseService] = [
    audio_service,
    video_service,
    microsof_service,
    flat_text_service,
    pdf_service,
]
url_service = URLService(services=services)


openai_settings = OpenAISettings()
client = openai.OpenAI(
    api_key=openai_settings.OPENAI_API_KEY,
    base_url=openai_settings.OPENAI_API_BASE,
)
model_context_length = openai_settings.MAX_TOKENS

summary_service = NaiveSummaryService(client=client, model_name=openai_settings.OPENAI_API_MODEL)


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

        if isinstance(task.content, URLModel):
            task = url_service.process_task(task=task)

        elif isinstance(task.content, DocumentModel):
            file_data = file_connector.get_by_task_id(user_id=task.user_id, task_id=task.id)
            with open(task.content.raw_filename, "wb") as f:
                f.write(file_data.read())
            task.content.file_path = task.content.raw_filename

            for service in services:
                if service.is_availble(task.content.content_type):
                    task = service.process_task(task=task)

            if os.path.exists(task.content.raw_filename):
                os.remove(task.content.raw_filename)

        elif isinstance(task.content, TextModel):
            task.result = ResultModel(
                type="flat",
                created_at=task.content.created_at,
                model_name="flat",
                model_version=__version__,
                percentage=1,
                texts_found=[task.content.text],
            )

        else:
            raise NotImplementedError("Content type not supported")

        splitted_text = split_texts_by_word_limit(
            [text for text in task.result.texts_found],
            max_words=int(model_context_length / 2),
        )
        task.result.texts_found = splitted_text
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
