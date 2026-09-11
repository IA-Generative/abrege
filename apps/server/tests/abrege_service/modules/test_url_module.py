from unittest.mock import patch
from abrege_service.modules.url import URLService
from src.schemas.task import TaskModel, TaskForm, task_table, TaskStatus
from src.schemas.content import URLModel
import pytest


def mock_task(url) -> TaskModel:
    task = task_table.insert_new_task(
        user_id="1",
        form_data=TaskForm(
            type="summary",
            status=TaskStatus.CREATED.value,
            updated_at=0,
            input=URLModel(created_at=0, url=url),
        ),
    )

    return task


def test_task_not_implemented():
    url_service = URLService()

    dummy_task = mock_task("https://this-is-tobi.com/")
    with (
        patch("abrege_service.modules.url.download_file", return_value="/tmp/downloaded_file"),
        patch("abrege_service.modules.url.get_content_type_from_file", return_value="text/html"),
        patch("abrege_service.modules.url.hash_file", return_value="abc123"),
    ):
        with pytest.raises(NotImplementedError):
            url_service.task_to_text(dummy_task)


def test_get_text_html():
    from abrege_service.modules.doc import HtmlToMdService

    url_service = URLService(services=[HtmlToMdService()])

    # Test donwload html
    dummy_task = mock_task("https://this-is-tobi.com/")

    actual = url_service.task_to_text(dummy_task)
    assert "Tobi's projects" in "\n".join([item for item in actual.output.texts_found])
