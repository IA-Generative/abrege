import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from unittest.mock import MagicMock
from api.routes.task import router
from src.schemas.task import TaskModel, task_table, TaskStatus


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


@pytest.fixture
def mock_task():
    return TaskModel(
        id="123",
        user_id="test_user",
        status=TaskStatus.CREATED.value,
        parameters=None,
        extras={},
        type="test",
        created_at=0,
        updated_at=0,
    )


def test_read_task(client, mock_task):
    task_table.get_task_by_id = MagicMock(return_value=mock_task)

    response = client.get("/task/123")
    assert response.status_code == 200
    assert response.json() == mock_task.dict()


def test_read_task_not_found(client):
    task_table.get_task_by_id = MagicMock(return_value=None)

    response = client.get("/task/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "999 not found"}


def test_read_user_tasks(client, mock_task):
    task_table.get_tasks_by_user_id = MagicMock(return_value=[mock_task])

    response = client.get("/task/user/test_user")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0] == mock_task.dict()


def test_read_user_tasks_empty(client):
    task_table.get_tasks_by_user_id = MagicMock(return_value=[])

    response = client.get("/task/user/test_user")
    assert response.status_code == 200
    assert response.json() == []
