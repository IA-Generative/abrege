import os
import pytest
from abrege_service.modules.ocr import OCRMIService
from src.schemas.task import TaskModel, TaskStatus, task_table, TaskForm
from src.schemas.content import DocumentModel

url = os.getenv("OCR_BACKEND_URL", "https://localhost:80/1")
is_ocr_client_available = True
try:
    obj_module_ocr = OCRMIService(url_ocr=url)
    obj_module_ocr.ocr_mi_client.get_health()
except Exception:
    is_ocr_client_available = False


@pytest.fixture(scope="module")
def dummy_task() -> TaskModel:
    task = task_table.insert_new_task(
        user_id="1",
        form_data=TaskForm(
            type="summary",
            status=TaskStatus.CREATED.value,
            updated_at=0,
            input=DocumentModel(
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


@pytest.mark.skipif(not is_ocr_client_available, reason=f"{url} is not available")
def test_integration_ocr_api(dummy_task: TaskModel):
    task = obj_module_ocr.task_to_text(task=dummy_task)
    assert task.status in TaskStatus.IN_PROGRESS.value
    assert task.output is not None
    assert task.output.percentage == 1
