import json
import pytest

from unittest.mock import patch
from fastapi.testclient import TestClient
from io import BytesIO
from api.routes.document_summary import doc_router
from src.models.task import TaskModel, TaskStatus


@pytest.fixture
def mock_file() -> BytesIO:
    content = b"Test file content"
    return BytesIO(content)


@pytest.fixture
def client(app_with_overrides):
    app = app_with_overrides(doc_router)
    return TestClient(app)


@pytest.fixture
def mock_created_task():
    return TaskModel(
        id="doc-123",
        user_id="dev",
        status=TaskStatus.CREATED.value,
        type="summary",
        extras={},
        created_at=1000,
        updated_at=1000,
    )


@patch("api.routes.document_summary.celery_app")
@patch("api.routes.document_summary.file_connector")
def test_summarize_doc(mock_fc, mock_celery, client, mock_task_service, mock_created_task, mock_file):
    mock_task_service.insert_new_task.return_value = mock_created_task
    mock_task_service.update_task.return_value = mock_created_task
    mock_fc.save.return_value = "/tmp/saved"

    form_data = {
        "prompt": None,
        "parameters": json.dumps({"key": "value"}),
    }
    files = {"file": ("test.pdf", mock_file, "application/pdf")}

    response = client.post("/task/document", data=form_data, files=files)

    assert response.status_code == 201
    assert "id" in response.json()


@patch("api.routes.document_summary.celery_app")
@patch("api.routes.document_summary.file_connector")
def test_summarize_doc_none_parameters_extras(mock_fc, mock_celery, client, mock_task_service, mock_created_task, mock_file):
    mock_task_service.insert_new_task.return_value = mock_created_task
    mock_task_service.update_task.return_value = mock_created_task
    mock_fc.save.return_value = "/tmp/saved"

    form_data = {
        "prompt": None,
        "parameters": None,
    }
    files = {"file": ("test.pdf", mock_file, "application/pdf")}

    response = client.post("/task/document", data=form_data, files=files)

    assert response.status_code == 201
    assert "id" in response.json()


@patch("api.routes.document_summary.celery_app")
@patch("api.routes.document_summary.file_connector")
def test_summarize_doc_no_valid_extras_or_paramters(mock_fc, mock_celery, client, mock_task_service, mock_created_task, mock_file):
    mock_task_service.insert_new_task.return_value = mock_created_task
    mock_task_service.update_task.return_value = mock_created_task
    mock_fc.save.return_value = "/tmp/saved"

    form_data = {
        "prompt": None,
        "parameters": json.dumps({"key": "value"}),
        "extras": "sq",
    }
    files = {"file": ("test.pdf", mock_file, "application/pdf")}

    response = client.post("/task/document", data=form_data, files=files)

    assert response.status_code == 201

    # Reset mock_file for second request
    mock_file.seek(0)

    form_data = {
        "prompt": None,
        "parameters": "sqi",
        "extras": json.dumps({"key": "value"}),
    }
    files = {"file": ("test.pdf", mock_file, "application/pdf")}

    response = client.post("/task/document", data=form_data, files=files)

    assert response.status_code == 422
