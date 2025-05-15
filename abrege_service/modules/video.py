import os
from uuid import uuid4
from abrege_service.schemas import VIDEO_CONTENT_TYPES
from abrege_service.modules.audio import AudioVoskTranscriptionService
from abrege_service.modules.base import BaseService
from src.schemas.task import TaskModel
from src.schemas.content import DocumentModel
from moviepy import VideoFileClip, AudioClip

folder_dest = os.environ.get("CACHE_FOLDER")


def extraire_audio(video_path, audio_path):
    clip = VideoFileClip(video_path)
    if clip.audio is not None:
        clip.audio.write_audiofile(audio_path)
    else:
        # Créer une piste audio silencieuse
        audio_silencieux = AudioClip(frame_function=lambda t: 0, duration=clip.duration)
        audio_silencieux.write_audiofile(audio_path, fps=44100)


class VideoBaseService(BaseService):
    def __init__(self, content_type_allowed=VIDEO_CONTENT_TYPES):
        super().__init__(content_type_allowed)


class VideoTranscriptionService(VideoBaseService):
    def __init__(self, service_ratio_representaion: float = 1):
        super().__init__()
        self.audio_service = AudioVoskTranscriptionService(service_ratio_representaion=service_ratio_representaion)

    def task_to_text(self, task: TaskModel, **kwargs) -> TaskModel:
        if not os.path.exists(task.content.file_path):
            raise FileExistsError(f"video {task.content.file_path} don't exist")

        tmp_file = f"{uuid4().hex}.wav"
        if folder_dest:
            tmp_file = os.path.join(folder_dest, tmp_file)

        extraire_audio(task.content.file_path, tmp_file)
        if not os.path.exists(tmp_file):
            raise FileExistsError(f"audio {tmp_file} create from video {task.content.file_path} don't exist")
        task_audio = task.model_copy()
        task_audio.content = DocumentModel(
            created_at=task.content.created_at,
            file_path=tmp_file,
            raw_filename=task.content.raw_filename,
            content_type="audio/wav",
            ext="wav",
            size=task.content.size,
        )
        task_audio = self.audio_service.task_to_text(task=task_audio)
        task.result = task_audio.result
        task.status = task_audio.status

        if os.path.exists(task.content.file_path):
            os.remove(task.content.file_path)
        if os.path.exists(tmp_file):
            os.remove(tmp_file)

        return task
