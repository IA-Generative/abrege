from typing import List, Union
import pymupdf4llm
from abrege_service.modules.base import BaseService
from markitdown import MarkItDown
from abrege_service.schemas import (
    PDF_CONTENT_TYPES,
    MICROSOFT_WORD_CONTENT_TYPES,
    MICROSOFT_SPREADSHEET_CONTENT_TYPES,
    MICROSOFT_PRESENTATION_CONTENT_TYPES,
    TEXT_CONTENT_TYPES,
)
from abrege_service.schemas.content_type_categories import ContentTypeCategories
from abrege_service.schemas.text import TextModel
from abrege_service.utils.content_type import get_content_category

md = MarkItDown(enable_plugins=False)


class DocService(BaseService):
    def is_availble(self, content_type: str) -> bool:
        """
        Check if the content type is available for processing.

        Args:
            content_type (str): The content type to check.

        Returns:
            bool: True if the content type is available for processing, False otherwise.
        """
        return (
            content_type
            in PDF_CONTENT_TYPES
            + MICROSOFT_WORD_CONTENT_TYPES
            + MICROSOFT_SPREADSHEET_CONTENT_TYPES
            + MICROSOFT_PRESENTATION_CONTENT_TYPES
            + TEXT_CONTENT_TYPES
        )

    def pdf_to_text(
        self,
        file_path: str,
        page_chunks: bool = True,
        embed_images: bool = True,
        **kwargs,
    ) -> Union[str, List[str]]:
        """
        Convert PDF to text.
        Args:
            file_path (str): The path to the PDF file.
            **kwargs: Additional arguments for processing.
        Returns:
            str: The processed result.
        """
        # Implement the logic to convert PDF to text
        # This is a placeholder implementation

        return pymupdf4llm.to_markdown(file_path, page_chunks=page_chunks, embed_images=embed_images)

    def word_to_text(self, file_path: str, **kwargs) -> str:
        """
        Convert Word document to text.
        Args:
            file_path (str): The path to the Word document.
            **kwargs: Additional arguments for processing.
        Returns:
            str: The processed result.
        """
        # Implement the logic to convert Word document to text
        # This is a placeholder implementation
        return md.convert(source=file_path).text_content

    def transform_to_text(self, file_path: str, content_type: str, **kwargs) -> List[TextModel]:
        """
        Transform the document to text.
        Args:
            file_path (str): The path to the file.
            content_type (str): The content type of the file.
            **kwargs: Additional arguments for processing.
        Returns:
            str: The processed result.
        """
        # Implement the logic to transform the document to text
        # This is a placeholder implementation
        category = get_content_category(content_type)
        if category == ContentTypeCategories.PDF.value:
            return [TextModel(text=item["text"], extras=item) for item in self.pdf_to_text(file_path, **kwargs)]

        if category == ContentTypeCategories.WORD_DOCUMENT.value:
            return [TextModel(text=self.word_to_text(file_path, **kwargs))]
        if category == ContentTypeCategories.TEXTE.value:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
                return [TextModel(text=file.read(), extras={})]

        raise NotImplementedError(f"Content type {content_type} is not implemented for {self.__class__.__name__}.")
