import os
import requests

from abrege_service.modules.audio import AudioBaseService
from abrege_service.modules.doc import DocService
from abrege_service.modules.video import VideoService
from abrege_service.modules.base import BaseService
from abrege_service.schemas.content_type_categories import ContentTypeCategories
from abrege_service.utils.content_type import (
    get_content_category,
    get_content_type_from_file,
)

from src.utils.url import check_url


class URLBaseService(BaseService):
    def is_availble(self, content_type: str) -> bool:
        """
        Check if the content type is available for processing.

        Args:
            content_type (str): The content type to check.

        Returns:
            bool: True if the content type is available for processing, False otherwise.
        """
        return True

    def is_valid_url(self, url: str) -> bool:
        """
        Check if the URL is valid.

        Args:
            url (str): The URL to check.

        Returns:
            bool: True if the URL is valid, False otherwise.
        """
        return check_url(url)


class URLService(URLBaseService):
    def __init__(
        self,
        audio_service: AudioBaseService,
        video_service: VideoService,
        doc_service: DocService,
    ):
        self.audio_service = audio_service
        self.video_service = video_service
        self.doc_service = doc_service

    def get_content_type(self, url: str) -> str:
        """
        Get the content type of the URL.

        Args:
            url (str): The URL to check.

        Returns:
            str: The content type of the URL.
        """
        try:
            response = requests.head(url, allow_redirects=True)
            content_type = response.headers.get("Content-Type")
            return content_type
        except requests.RequestException as e:
            print(f"Erreur lors de la requête : {e}")

    def download_file(self, url: str, filename=None):
        try:
            with requests.get(url, stream=True) as response:
                response.raise_for_status()
                filename = url.split("/")[-1] or "downloaded_file"
                with open(filename, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:  # filtrer les keep-alive
                            f.write(chunk)
            return filename
        except requests.RequestException as e:
            print(f"Erreur lors du téléchargement : {e}")

    def transform_to_text(self, file_path: str, **kwargs) -> str:
        assert self.is_valid_url(file_path), f"{file_path} is not a valid URL"
        filename = self.download_file(url=file_path)
        content_type_calculated = get_content_type_from_file(filename)
        category = get_content_category(content_type=content_type_calculated)
        if category in [
            ContentTypeCategories.PDF.value,
            ContentTypeCategories.WORD_DOCUMENT.value,
            ContentTypeCategories.TEXTE.value,
        ]:
            return self.doc_service.transform_to_text(filename, content_type=content_type_calculated)
        if category in [ContentTypeCategories.AUDIO.value]:
            return self.audio_service.transform_to_text(file_path=filename, content_type=content_type_calculated)

        if category in [ContentTypeCategories.VIDEO.value]:
            return self.video_service.transform_to_text(file_path=filename, content_type=content_type_calculated)
        if os.path.exists(filename):
            os.remove(filename)

        raise NotImplementedError(f"{file_path} can not be abrege - {category} - {content_type_calculated}")
