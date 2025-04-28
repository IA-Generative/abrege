import os
from abc import abstractmethod

from abrege_service.schemas import VIDEO_CONTENT_TYPES
from abrege_service.modules.audio import AudioBaseService
from abrege_service.modules.base import BaseService
from abrege_service.schemas.text import TextModel
from typing import List
from moviepy import VideoFileClip


def extraire_audio(video_path, audio_path):
    clip = VideoFileClip(video_path)
    if clip is not None and clip.audio is not None:
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

    def video_audio_to_text(self, file_path: str, **kwargs) -> List[TextModel]:
        return self.audio_service.transform_to_text(
            file_path,
            content_type="audio/wav",
            **kwargs,
        )

    def video_to_text(self, file_path: str, **kwargs) -> List[TextModel]:
        """
        Convert video to text.
        Args:
            file_path (str): The path to the video file.
            **kwargs: Additional arguments for processing.
        Returns:
            str: The processed result.
        """
        return []

    def transform_to_text(self, file_path, content_type, **kwargs) -> List[TextModel]:
        extraire_audio(file_path, "temp.wav")
        if not self.is_availble(content_type):
            raise NotImplementedError(f"Content type {content_type} is not implemented for {self.__class__.__name__}.")
        result_audio = []
        if os.path.exists("temp.wav"):
            result_audio = self.audio_service.transform_to_text(
                "temp.wav",
                content_type="audio/wav",
                **kwargs,
            )
        result = {
            "video_audio_transcription": result_audio,
            "video_description": self.video_to_text(file_path, **kwargs),
        }
        text_result = []
        for key in result:
            for text in result[key]:
                text_result.append(text.text)
        text_result = "\n".join(text_result)
        return [TextModel(text=text_result, extras=result)]
