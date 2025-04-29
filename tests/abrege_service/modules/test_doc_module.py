import pathlib
from abrege_service.modules.doc import DocService
import pytest


def test_doc_service():
    doc_service = DocService(audio_service=None, video_service=None)

    # Test for PDF content type
    assert doc_service.is_availble("application/pdf") is True

    # Test for Microsoft Word content type
    assert doc_service.is_availble("application/vnd.openxmlformats-officedocument.wordprocessingml.document") is True

    # Test for Image content type
    assert doc_service.is_availble("image/jpeg") is False

    # Get the content into a markdown file
    # For pymupdf4llm
    md_text = doc_service.pdf_to_text("tests/test_data/2106.11520v2.pdf", page_chunks=False)
    pathlib.Path("tests/data/2106.11520v2.md").write_bytes(md_text.encode())
    # For markitdown
    # 2106.11520v2.pdf is a pdf file with images
    md_text = doc_service.word_to_text("tests/test_data/2106.11520v2.pdf")
    pathlib.Path("tests/data/2106.11520v2-markitdown.md").write_bytes(md_text.encode())

    md_text = doc_service.word_to_text("tests/test_data/Cadrage.docx")
    pathlib.Path("tests/data/Cadrage-markitdown.md").write_bytes(md_text.encode())

    # Test page number
    md_text = doc_service.pdf_to_text("tests/test_data/2106.11520v2.pdf", page_chunks=True)
    assert len(md_text) == 18
    # Test pdf to text
    actual = doc_service.transform_to_text(file_path="tests/test_data/2106.11520v2.pdf", content_type="application/pdf")

    assert len(actual) == 18
    # test word to text
    actual = doc_service.transform_to_text(
        file_path="tests/test_data/Cadrage.docx",
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

    assert len(actual) == 1

    with pytest.raises(NotImplementedError):
        doc_service.transform_to_text(
            file_path="tests/test_data/2106.11520v2.pdf",
            content_type="dsds/mp4",
        )
