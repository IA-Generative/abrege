from abrege_service.modules.audio import AudioService
from abrege_service.modules.doc import DocService
from abrege_service.modules.video import VideoService
from abrege_service.modules.url import URLService
from abrege_service.schemas.text import TextModel as TextModelService
from src.schemas.task import TaskModel
from src.schemas.content import URLModel, DocumentModel, TextModel
from abrege_service.models.summary.naive import process_documents

document_service = DocService()
audio_service = AudioService()
video_service = VideoService()
url_service = URLService(audio_service=audio_service, video_service=video_service, doc_service=document_service)


def launch(task: dict):
    task: TaskModel = TaskModel.model_validate(task)
    if isinstance(task.content, URLModel):
        texts = url_service.transform_to_text(file_path=task.content.url)

    elif isinstance(task.content, DocumentModel):
        texts = document_service.transform_to_text(task.content.file_path, content_type=task.content.content_type)

    elif isinstance(task.content, TextModel):
        texts = [TextModelService(text=task.content, extras=task.model_dump())]

    else:
        raise Exception("")

    process_documents(docs=[text.text for text in texts], model="", client=None, size=500, langage="")
