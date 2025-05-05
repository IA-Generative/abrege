from abrege_service.modules.doc import PDFTOMD4LLMService, MicrosoftDocumnentToMdService
from src.schemas.task import TaskModel, TaskForm, task_table, TaskStatus
from src.schemas.content import DocumentModel
import pytest


@pytest.fixture(scope="module")
def dummy_task() -> TaskModel:
    task = task_table.insert_new_task(
        user_id="1",
        form_data=TaskForm(
            type="summary",
            status=TaskStatus.CREATED.value,
            updated_at=0,
            content=DocumentModel(
                created_at=0,
                file_path="tests/test_data/elysee-module-24161-fr.pdf",
                raw_filename="elysee-module-24161-fr.pdf",
                content_type="application/pdf",
                ext=".pdf",
                size=2,
            ),
        ),
    )

    return task


@pytest.fixture(scope="module")
def dummy_task_microsoft() -> TaskModel:
    task = task_table.insert_new_task(
        user_id="1",
        form_data=TaskForm(
            type="summary",
            status=TaskStatus.CREATED.value,
            updated_at=0,
            content=DocumentModel(
                created_at=0,
                file_path="tests/test_data/Cadrage.docx",
                raw_filename="Cadrage.docx",
                content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                ext=".docx",
                size=2,
            ),
        ),
    )

    return task


def test_doc_service_pdf(dummy_task: TaskModel):
    doc_service = PDFTOMD4LLMService()
    task = doc_service.task_to_text(task=dummy_task)
    assert task.result.percentage == 1
    assert len(task.result.texts_found) == 3


def test_doc_service_microft(dummy_task_microsoft: TaskModel):
    doc_service = MicrosoftDocumnentToMdService()
    task = doc_service.task_to_text(task=dummy_task_microsoft)
    assert task.result.percentage == 1
    assert len(task.result.texts_found) == 1
