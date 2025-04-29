import os
import time
import json

import openai

from abrege_service.modules.audio import AudioService
from abrege_service.modules.doc import DocService
from abrege_service.modules.video import VideoService
from abrege_service.modules.url import URLService
from abrege_service.schemas.text import TextModel as TextModelService
from abrege_service.models.summary.naive import merge_summaries
from abrege_service.utils.text import split_texts_by_word_limit
from abrege_service.config.openai import OpenAISettings

from src.schemas.task import TaskModel, task_table, TaskStatus, TaskUpdateForm
from src.schemas.content import URLModel, DocumentModel, TextModel
from src.clients import celery_app, file_connector


audio_service = AudioService()
video_service = VideoService(audio_service=audio_service)
document_service = DocService(audio_service=audio_service, video_service=video_service)
# TODO: transform to url service to use only doc service for document process
url_service = URLService(
    audio_service=audio_service,
    video_service=video_service,
    doc_service=document_service,
)


openai_settings = OpenAISettings()
client = openai.OpenAI(
    api_key=openai_settings.OPENAI_API_KEY,
    base_url=openai_settings.OPENAI_API_BASE,
)
model_context_length = openai_settings.MAX_TOKENS


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
            texts = url_service.transform_to_text(file_path=task.content.url)

        elif isinstance(task.content, DocumentModel):
            file_data = file_connector.get_by_task_id(user_id=task.user_id, task_id=task.id)
            with open(task.content.raw_filename, "wb") as f:
                f.write(file_data.read())
            texts = document_service.transform_to_text(task.content.raw_filename, content_type=task.content.content_type)
            if os.path.exists(task.content.raw_filename):
                os.remove(task.content.raw_filename)

        elif isinstance(task.content, TextModel):
            texts = [TextModelService(text=task.content.text, extras=task.content.model_dump())]

        else:
            raise NotImplementedError("Content type not supported")

        task.extras["texts"] = [text.model_dump() for text in texts]
        task_table.update_task(
            task_id=task.id,
            form_data=TaskUpdateForm(
                status=TaskStatus.IN_PROGRESS.value,
                updated_at=int(time.time()),
                extras=task.extras,
            ),
        )

        splitted_text = split_texts_by_word_limit([text.text for text in texts], max_words=int(model_context_length / 2))

        task, _ = merge_summaries(
            task=task,
            summaries=splitted_text,
            model=task.extras.get("model_name", openai_settings.OPENAI_API_MODEL),
            client=client,
            size=task.extras.get("max_word", 4000),
            language=task.extras.get("language", "français"),
            tempature=task.extras.get("temperature", 0.0),
        )
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
