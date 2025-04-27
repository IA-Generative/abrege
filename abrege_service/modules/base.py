from abc import ABC, abstractmethod


class BaseService(ABC):
    @abstractmethod
    def is_availble(self, content_type: str) -> bool: ...

    @abstractmethod
    def transform_to_text(self, file_path: str, content_type: str, **kwargs) -> str: ...

    def process(self, file_path: str, content_type: str, **kwargs):
        """
        Process the file and return the result.

        Args:
            file_path (str): The path to the file.
            content_type (str): The content type of the file.
            **kwargs: Additional arguments for processing.

        Returns:
            str: The processed result.
        """
        if not self.is_availble(content_type):
            raise ValueError(f"Content type {content_type} is not available for processing.")
        return self.transform_to_text(file_path, content_type, **kwargs)
