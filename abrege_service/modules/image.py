from abrege_service.schemas import IMAGE_CONTENT_TYPES
from abrege_service.modules.base import BaseService


class ImageService(BaseService):
    def is_availble(self, content_type: str) -> bool:
        """
        Check if the content type is available for processing.

        Args:
            content_type (str): The content type to check.

        Returns:
            bool: True if the content type is available for processing, False otherwise.
        """
        return content_type in IMAGE_CONTENT_TYPES

    def image_to_text(self, file_path: str, **kwargs) -> str:
        raise NotImplementedError("Image to text conversion is not implemented.")

    def transform_to_text(self, file_path, content_type, **kwargs) -> str:
        if not self.is_availble(content_type):
            raise NotImplementedError(f"Content type {content_type} is not implemented for {self.__class__.__name__}.")

        return self.image_to_text(file_path, **kwargs)
