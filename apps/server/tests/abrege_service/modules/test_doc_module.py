from abrege_service.modules.doc import HtmlToMdService, MicrosoftOlderDocumentToMdService
from src.schemas.task import TaskModel, TaskForm, task_table, TaskStatus
from src.schemas.content import DocumentModel
import pytest


@pytest.fixture(scope="module")
def dummy_task_doc() -> TaskModel:
    task = task_table.insert_new_task(
        user_id="1",
        form_data=TaskForm(
            type="summary",
            status=TaskStatus.CREATED.value,
            updated_at=0,
            input=DocumentModel(
                created_at=0,
                file_path="tests/test_data/tabFicSol2.doc",
                raw_filename="tabFicSol2.doc",
                content_type="application/msword",
                ext="doc",
                size=2,
            ),
        ),
    )

    return task


def test_doc_service_doc(dummy_task_doc: TaskModel):
    doc_service = MicrosoftOlderDocumentToMdService()
    task = doc_service.task_to_text(task=dummy_task_doc)
    assert task.output.percentage == 1
    assert len(task.output.texts_found) == 1


def test_html_service_content_type_allowed():
    service = HtmlToMdService()
    assert service.content_type_allowed == ["text/html"]
