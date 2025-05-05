from unittest.mock import patch
from abrege_service.modules.ocr import OCRMIService
from src.schemas.task import TaskModel, TaskStatus, task_table, TaskForm
from src.schemas.content import DocumentModel


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


@patch("abrege_service.modules.ocr.OCRClient")
def test_task_to_text_with_mocked_ocr_client(MockOCRClient: OCRMIService):
    # 1. Mock OCRClient instance
    mock_client = MockOCRClient.return_value

    # Mock get_health() return
    mock_client.get_health.return_value.name = "mock-model"
    mock_client.get_health.return_value.version = "1.0"

    # Mock send() -> returns initial OCR task
    mock_client.send.return_value = {"id": "abc123", "status": TaskStatus.CREATED.value}

    # Mock get_tasks() -> simulates progress, then completion
    mock_client.get_tasks.side_effect = [
        {
            "id": "abc123",
            "status": TaskStatus.IN_PROGRESS.value,
            "percentage": 0.5,
            "output": {"pages": [{"bboxes": [{"text": "Hello"}, {"text": "World"}]}]},
        },
        {
            "id": "abc123",
            "status": TaskStatus.COMPLETED.value,
            "percentage": 1,
            "output": {"pages": [{"bboxes": [{"text": "Hello"}, {"text": "World"}]}]},
        },
    ]

    task = dummy_task()

    # 3. Instancier le service
    service = OCRMIService(url_ocr="http://fake-ocr")

    # 4. Appeler task_to_text()
    result_task = service.task_to_text(task)

    # 5. Vérifications
    assert result_task.result.percentage == 1
    assert result_task.result.texts_found == ["Hello", "World"]
    assert result_task.status == TaskStatus.IN_PROGRESS.value

    mock_client.send.assert_called_once()
    assert mock_client.get_tasks.call_count >= 1
