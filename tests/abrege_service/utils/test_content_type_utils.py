from abrege_service.schemas import ALL_CONTENT_TYPES
from abrege_service.utils.content_type import (
    is_content_type_available_for_process,
    get_content_category,
)


def test_is_content_type_available_for_process():
    for content_type in ALL_CONTENT_TYPES:
        assert is_content_type_available_for_process(content_type) is True
    assert is_content_type_available_for_process("application/unknown") is False


def test_get_content_category():
    # Test for PDF content type
    assert get_content_category("application/pdf") == "pdf"

    # Test for Microsoft Word content type
    assert get_content_category("application/vnd.openxmlformats-officedocument.wordprocessingml.document") == "word_document"

    # Test for Image content type
    assert get_content_category("image/jpeg") == "image"

    # Test for Audio content type
    assert get_content_category("audio/mpeg") == "audio"

    # Test for Archive content type
    assert get_content_category("application/zip") == "archive"

    # Test for Text content type
    assert get_content_category("text/plain") == "texte"

    # Test for Video content type
    assert get_content_category("video/mp4") == "video"

    # Test for unknown content type
    assert get_content_category("application/unknown") == "other"
