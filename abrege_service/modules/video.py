from abrege_service.schemas import VIDEO_CONTENT_TYPES
from abrege_service.modules.audio import AudioVoskTranscriptionService
from abrege_service.modules.base import BaseService
from src.schemas.task import TaskModel
from src.schemas.content import DocumentModel
from moviepy import VideoFileClip


def extraire_audio(video_path, audio_path):
    clip = VideoFileClip(video_path)
    if clip is not None and clip.audio is not None:
        clip.audio.write_audiofile(audio_path)


class VideoBaseService(BaseService):
    def __init__(self, content_type_allowed=VIDEO_CONTENT_TYPES):
        super().__init__(content_type_allowed)


class VideoTranscriptionService(VideoBaseService):
    def __init__(self, service_ratio_representaion: float = 1):
        super().__init__()
        self.audio_service = AudioVoskTranscriptionService(service_ratio_representaion=service_ratio_representaion)

    def task_to_text(self, task: TaskModel, **kwargs) -> TaskModel:
        extraire_audio(task.content.file_path, "temp.wav")
        task.content = DocumentModel(
            created_at=task.content.created_at,
            file_path="temp.wav",
            raw_filename=task.content.raw_filename,
            content_type="audio/wav",
            ext="wav",
            size=task.content.size,
        )

        return self.audio_service.task_to_text(task=task)
