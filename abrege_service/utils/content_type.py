import magic
import zipfile
from abrege_service.schemas import (
    IMAGE_CONTENT_TYPES,
    PDF_CONTENT_TYPES,
    MICROSOFT_WORD_CONTENT_TYPES,
    MICROSOFT_SPREADSHEET_CONTENT_TYPES,
    MICROSOFT_PRESENTATION_CONTENT_TYPES,
    AUDIO_CONTENT_TYPES,
    ARCHIVE_CONTENT_TYPES,
    TEXT_CONTENT_TYPES,
    ALL_CONTENT_TYPES,
)
from abrege_service.schemas.content_type_categories import ContentTypeCategories


def is_content_type_available_for_process(content_type: str) -> bool:
    """
    Check if the content type is available for processing.

    Args:
        content_type (str): The content type to check.

    Returns:
        bool: True if the content type is available for processing, False otherwise.
    """
    return content_type in ALL_CONTENT_TYPES


def get_content_category(content_type: str) -> str:
    if content_type in PDF_CONTENT_TYPES:
        return ContentTypeCategories.PDF.value
    if content_type in MICROSOFT_WORD_CONTENT_TYPES + MICROSOFT_PRESENTATION_CONTENT_TYPES + MICROSOFT_SPREADSHEET_CONTENT_TYPES:
        return ContentTypeCategories.WORD_DOCUMENT.value

    if content_type in IMAGE_CONTENT_TYPES:
        return ContentTypeCategories.IMAGE.value

    if content_type in AUDIO_CONTENT_TYPES:
        return ContentTypeCategories.AUDIO.value
    if content_type in ARCHIVE_CONTENT_TYPES:
        return ContentTypeCategories.ARCHIVE.value
    if content_type in TEXT_CONTENT_TYPES:
        return ContentTypeCategories.TEXTE.value
    if content_type.startswith("video/"):
        return ContentTypeCategories.VIDEO.value
    return ContentTypeCategories.OTHER.value


def get_content_type_from_file(file_name: str) -> str:
    mime = magic.Magic(mime=True)

    mime_type = mime.from_file(filename=file_name)

    if mime_type == "application/zip":
        try:
            with zipfile.ZipFile(file_name, "r") as archive:
                files = archive.namelist()
                if "word/document.xml" in files:
                    return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                elif "xl/workbook.xml" in files:
                    return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                elif "ppt/presentation.xml" in files:
                    return "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        except zipfile.BadZipFile:
            pass
    return mime_type
