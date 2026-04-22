import pytest
from fastapi.testclient import TestClient
from api.routes.task import router
from src.models.task import TaskModel, TaskStatus


@pytest.fixture
def mock_task():
    return TaskModel(
        id="123",
        user_id="dev",
        status=TaskStatus.CREATED.value,
        parameters=None,
        extras={},
        type="test",
        created_at=0,
        updated_at=0,
    )


@pytest.fixture
def client(app_with_overrides):
    app = app_with_overrides(router)
    return TestClient(app)


def test_read_task(client, mock_task_service, mock_task):
    mock_task_service.get_task_by_id.return_value = mock_task
    mock_task_service.get_position_in_queue.return_value = None

    response = client.get("/task/123")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "123"


def test_read_task_not_found(client, mock_task_service):
    mock_task_service.get_task_by_id.return_value = None

    response = client.get("/task/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "999 not found"}


def test_read_user_tasks(client, mock_task_service, mock_task):
    mock_task_service.get_tasks_by_user_id.return_value = [mock_task]
    mock_task_service.count_tasks_by_user_id.return_value = 1

    response = client.get("/task/user/")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1


def test_read_user_tasks_empty(client, mock_task_service):
    mock_task_service.get_tasks_by_user_id.return_value = []
    mock_task_service.count_tasks_by_user_id.return_value = 0

    response = client.get("/task/user/")
    assert response.status_code == 200
    assert response.json()["items"] == []
