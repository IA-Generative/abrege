import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from api.routes.summarize import router
from src.models.task import TaskModel, TaskStatus


@pytest.fixture
def client(app_with_overrides):
    app = app_with_overrides(router)
    return TestClient(app)


@pytest.fixture
def mock_created_task():
    return TaskModel(
        id="abc-123",
        user_id="dev",
        status=TaskStatus.CREATED.value,
        type="summary",
        created_at=1000,
        updated_at=1000,
    )


@patch("api.routes.summarize.celery_app")
def test_summarize_content_url(mock_celery, client, mock_task_service, mock_created_task):
    mock_task_service.insert_new_task.return_value = mock_created_task
    mock_celery.send_task = AsyncMock()

    response = client.post(
        "/task/text-url",
        json={
            "user_id": "test",
            "content": {
                "url": "https://google.com",
                "extras": {"key": "value"},
                "prompt": "Summarize this page",
            },
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert "created_at" in data
    assert TaskModel.model_validate(data)


@patch("api.routes.summarize.celery_app")
def test_summarize_content_text(mock_celery, client, mock_task_service, mock_created_task):
    mock_task_service.insert_new_task.return_value = mock_created_task
    mock_celery.send_task = AsyncMock()

    response = client.post(
        "/task/text-url",
        json={
            "user_id": "test",
            "content": {
                "text": "https://example.com",
                "extras": {"key": "value"},
                "prompt": "Summarize this page",
            },
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert "created_at" in data
    assert TaskModel.model_validate(data)


def test_summarize_content_body_error(client):
    response = client.post(
        "/task/text-url",
        json={
            "content": {
                "stext": "https://example.com",
                "extras": {"key": "value"},
                "prompt": "Summarize this page",
            }
        },
    )

    assert response.status_code == 400, response.json()


def test_summarize_content_url_error(client, mock_task_service):
    response = client.post(
        "/task/text-url",
        json={
            "user_id": "test_user",
            "content": {
                "url": "https://22222.24",
                "prompt": "Summarize this page",
                "extras": {"key": "value"},
            },
        },
    )

    assert response.status_code == 500
