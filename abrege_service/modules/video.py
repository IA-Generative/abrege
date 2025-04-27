from abc import abstractmethod
import json

from abrege_service.schemas import VIDEO_CONTENT_TYPES
from abrege_service.schemas.audio import AudioModel
from abrege_service.modules.audio import AudioBaseService
from abrege_service.modules.base import BaseService
from typing import List
from moviepy import VideoFileClip


def extraire_audio(video_path, audio_path):
    clip = VideoFileClip(video_path)
    clip.audio.write_audiofile(audio_path)


class VideoBaseService(BaseService):
    def is_availble(self, content_type: str) -> bool:
        """
        Check if the content type is available for processing.

        Args:
            content_type (str): The content type to check.

        Returns:
            bool: True if the content type is available for processing, False otherwise.
        """
        return content_type in VIDEO_CONTENT_TYPES

    @abstractmethod
    def video_audio_to_text(self, file_path: str, **kwargs) -> str: ...

    @abstractmethod
    def video_to_text(self, file_path: str, **kwargs) -> str: ...


class VideoService(VideoBaseService):
    def __init__(self, audio_service: AudioBaseService):
        self.audio_service = audio_service

    def video_audio_to_text(self, file_path: str, **kwargs) -> List[AudioModel]:
        return self.audio_service.transform_to_text(
            file_path,
            content_type="audio/wav",
            **kwargs,
        )

    def video_to_text(self, file_path: str, **kwargs) -> str:
        """
        Convert video to text.
        Args:
            file_path (str): The path to the video file.
            **kwargs: Additional arguments for processing.
        Returns:
            str: The processed result.
        """
        return ""

    def transform_to_text(self, file_path, content_type, **kwargs) -> str:
        extraire_audio(file_path, "temp.wav")
        if not self.is_availble(content_type):
            raise NotImplementedError(f"Content type {content_type} is not implemented for {self.__class__.__name__}.")
        result = {
            "video_audio_transcription": self.audio_service.transform_to_text(
                "temp.wav",
                content_type="audio/wav",
                **kwargs,
            ),
            "video_description": self.video_to_text(file_path, **kwargs),
        }
        return json.dumps(result, ensure_ascii=False)
