import os
import pytest
from abrege_service.modules.ocr import OCRMIService
from abrege_service.schemas import AUDIO_CONTENT_TYPES, VIDEO_CONTENT_TYPES
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


def test_content_type_allowed_includes_audio_and_video(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("OCR_API_KEY", "test-key")  # bypass the Keycloak-config check
    service = OCRMIService(url_ocr=url)

    assert set(AUDIO_CONTENT_TYPES).issubset(service.content_type_allowed)
    assert set(VIDEO_CONTENT_TYPES).issubset(service.content_type_allowed)


@pytest.mark.parametrize("content_type,ext", [("audio/wav", ".wav"), ("video/mp4", ".mp4")])
def test_audio_and_video_are_sent_as_a_single_file_not_rasterized(monkeypatch: pytest.MonkeyPatch, content_type, ext):
    """Audio/video have no per-page structure: the whole file must be sent to the OCR
    backend as one job, unlike a PDF which gets rasterized into per-page images first."""
    monkeypatch.setenv("OCR_API_KEY", "test-key")  # bypass the Keycloak-config check
    task = task_table.insert_new_task(
        user_id="1",
        form_data=TaskForm(
            type="summary",
            status=TaskStatus.CREATED.value,
            updated_at=0,
            input=DocumentModel(
                created_at=0,
                file_path=f"tests/data/dummy{ext}",
                raw_filename=f"dummy{ext}",
                content_type=content_type,
                ext=ext,
                size=2,
            ),
        ),
    )

    service = OCRMIService(url_ocr=url)
    monkeypatch.setattr(service.ocr_mi_client, "get_health", lambda: {"name": "ocr", "version": "1"})
    sent_paths = []
    monkeypatch.setattr(
        service.ocr_mi_client,
        "send",
        lambda file_path, group_id="abrege": (sent_paths.append(file_path), {"id": "ocr-task-1"})[1],
    )
    monkeypatch.setattr(
        service.ocr_mi_client,
        "get_tasks",
        lambda task_id: {"status": TaskStatus.COMPLETED.value, "output": None},
    )

    service.task_to_text(task=task)

    assert sent_paths == [task.input.file_path]
