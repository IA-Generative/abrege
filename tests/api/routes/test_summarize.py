from fastapi.testclient import TestClient
from fastapi import FastAPI

from api.routes.summarize import router
from src.schemas.task import TaskModel


def test_summarize_content_url():
    app = FastAPI()
    app.include_router(router)

    client = TestClient(app)
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


def test_summarize_content_text():
    app = FastAPI()
    app.include_router(router)

    client = TestClient(app)
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


def test_summarize_content_body_error():
    app = FastAPI()
    app.include_router(router)

    client = TestClient(app)
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

    assert response.status_code == 422


def test_summarize_content_url_error():
    app = FastAPI()
    app.include_router(router)
    input_data = {
        "user_id": "test_user",
        "content": {
            "url": "https://22222.24",  # URL invalide
            "prompt": "Summarize this page",
            "extras": {"key": "value"},
        },
    }

    client = TestClient(app)
    response = client.post("/task/text-url", json=input_data)

    assert response.status_code == 500
