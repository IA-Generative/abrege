from enum import Enum


class ContentTypeCategories(str, Enum):
    """
    Enum for content type categories.
    """

    PDF = "pdf"
    WORD_DOCUMENT = "word_document"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    ARCHIVE = "archive"
    TEXTE = "texte"
    OTHER = "other"
