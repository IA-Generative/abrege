from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from unittest.mock import MagicMock
from api.routes.task import router
from api.core.security.factory import TokenVerifier
from api.core.security.internal import verify_internal_service
from src.clients import celery_app
from src.schemas.entity import entity_table
from src.schemas.qa_item import qa_item_table
from src.schemas.task import TaskModel, task_table, TaskStatus


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


@pytest.fixture
def internal_client():
    """A client where the internal-service auth dependency is bypassed, to test the
    worker-only CRUD routes (POST /task/{id}/qa, /entities, /relationships/global) in
    isolation from the shared-secret check (covered separately in test_internal.py)."""
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[verify_internal_service] = lambda: None
    return TestClient(app)


def mock_verify_dev(ctx) -> bool:
    ctx.user_id = "dev"
    return True


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


def test_read_task(client, mock_task):
    task_table.get_task_by_id = MagicMock(return_value=mock_task)

    def mock_verify(ctx) -> bool:
        ctx.user_id = "dev"
        return True

    TokenVerifier.verify = mock_verify

    response = client.get("/task/123")
    assert response.status_code == 201
    assert response.json() == mock_task.dict()


def test_read_task_not_found(client):
    task_table.get_task_by_id = MagicMock(return_value=None)
    TokenVerifier.verify = MagicMock(return_value=True)

    response = client.get("/task/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "999 not found"}


def test_read_user_tasks(client, mock_task):
    task_table.get_tasks_by_user_id = MagicMock(return_value=[mock_task])
    TokenVerifier.verify = MagicMock(return_value=True)

    response = client.get("/task/user/")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
    assert response.json()["items"][0] == mock_task.dict()


def test_read_user_tasks_empty(client):
    task_table.get_tasks_by_user_id = MagicMock(return_value=[])
    TokenVerifier.verify = MagicMock(return_value=True)

    response = client.get("/task/user/")
    assert response.status_code == 200


def test_get_task_qa_items(client, mock_task):
    task_table.get_task_by_id = MagicMock(return_value=mock_task)
    TokenVerifier.verify = mock_verify_dev
    qa_item_table.get_qa_items_by_task = MagicMock(
        return_value=[
            SimpleNamespace(
                id="qa-1",
                task_id=mock_task.id,
                chunk_index=0,
                page=1,
                source_text="src",
                question="Q1",
                answer="A1",
                created_at=0,
            )
        ]
    )

    response = client.get(f"/task/{mock_task.id}/qa")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": "qa-1",
            "task_id": mock_task.id,
            "chunk_index": 0,
            "page": 1,
            "source_text": "src",
            "question": "Q1",
            "answer": "A1",
            "created_at": 0,
        }
    ]


def test_get_task_qa_items_not_found(client):
    task_table.get_task_by_id = MagicMock(return_value=None)
    TokenVerifier.verify = MagicMock(return_value=True)

    response = client.get("/task/missing/qa")

    assert response.status_code == 404


def test_get_task_entities(client, mock_task):
    task_table.get_task_by_id = MagicMock(return_value=mock_task)
    TokenVerifier.verify = mock_verify_dev
    entity_table.get_entities_by_task = MagicMock(
        return_value=[
            SimpleNamespace(
                id="ent-1",
                task_id=mock_task.id,
                chunk_index=0,
                type="PERSON",
                text="Alice",
                contexts=["ctx"],
                pages=[1],
                created_at=0,
            )
        ]
    )

    response = client.get(f"/task/{mock_task.id}/entities")

    assert response.status_code == 200
    assert response.json()[0]["text"] == "Alice"
    assert response.json()[0]["pages"] == [1]


def test_get_task_relationships(client, mock_task):
    task_table.get_task_by_id = MagicMock(return_value=mock_task)
    TokenVerifier.verify = mock_verify_dev
    entity_table.get_relationships_by_task = MagicMock(
        return_value=[
            SimpleNamespace(
                id="rel-1",
                task_id=mock_task.id,
                chunk_index=None,
                source_entity_id="ent-1",
                target_entity_id="ent-2",
                relationship_type="WORKS_AT",
                description="desc",
                created_at=0,
            )
        ]
    )

    response = client.get(f"/task/{mock_task.id}/relationships")

    assert response.status_code == 200
    assert response.json()[0]["source_entity_id"] == "ent-1"
    assert response.json()[0]["chunk_index"] is None


def test_extract_task_details_triggers_extraction_for_completed_task(client):
    mock_task = TaskModel(
        id="123",
        user_id="dev",
        status=TaskStatus.COMPLETED.value,
        type="summary",
        created_at=0,
        updated_at=0,
        output=None,
    )
    mock_task.output = MagicMock(texts_found=["some text"])
    task_table.get_task_by_id = MagicMock(return_value=mock_task)
    TokenVerifier.verify = mock_verify_dev
    celery_app.send_task = MagicMock()

    response = client.post("/task/123/extract-details")

    assert response.status_code == 202
    assert response.json() == {"task_id": "123", "status": "extraction_queued"}
    celery_app.send_task.assert_called_once_with("worker.tasks.extract_task_details", args=["123"])


def test_extract_task_details_rejects_non_completed_task(client):
    mock_task = TaskModel(
        id="123",
        user_id="dev",
        status=TaskStatus.IN_PROGRESS.value,
        type="summary",
        created_at=0,
        updated_at=0,
    )
    task_table.get_task_by_id = MagicMock(return_value=mock_task)
    TokenVerifier.verify = mock_verify_dev

    response = client.post("/task/123/extract-details")

    assert response.status_code == 400


def test_extract_task_details_rejects_task_without_source_text(client):
    mock_task = TaskModel(
        id="123",
        user_id="dev",
        status=TaskStatus.COMPLETED.value,
        type="summary",
        created_at=0,
        updated_at=0,
        output=None,
    )
    task_table.get_task_by_id = MagicMock(return_value=mock_task)
    TokenVerifier.verify = mock_verify_dev

    response = client.post("/task/123/extract-details")

    assert response.status_code == 400


def test_extract_task_details_not_found(client):
    task_table.get_task_by_id = MagicMock(return_value=None)
    TokenVerifier.verify = MagicMock(return_value=True)

    response = client.post("/task/missing/extract-details")

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Internal (worker-only) CRUD routes
# ---------------------------------------------------------------------------


def test_create_task_qa_items_saves_the_chunk(internal_client):
    task_table.get_task_by_id = MagicMock(return_value=SimpleNamespace(id="123"))
    qa_item_table.save_chunk_qa_items = MagicMock()

    response = internal_client.post(
        "/task/123/qa",
        json={"chunk_index": 2, "qa_items": [{"page": 1, "source_text": "src", "question": "Q1", "answer": "A1"}]},
    )

    assert response.status_code == 201
    assert response.json() == {"task_id": "123", "chunk_index": 2, "status": "saved"}
    args, kwargs = qa_item_table.save_chunk_qa_items.call_args
    assert kwargs["task_id"] == "123"
    assert kwargs["chunk_index"] == 2
    assert kwargs["qa_items"][0].question == "Q1"


def test_create_task_qa_items_requires_internal_auth(client):
    response = client.post("/task/123/qa", json={"chunk_index": 0, "qa_items": []})
    assert response.status_code == 401


def test_create_task_qa_items_task_not_found(internal_client):
    task_table.get_task_by_id = MagicMock(return_value=None)

    response = internal_client.post("/task/missing/qa", json={"chunk_index": 0, "qa_items": []})

    assert response.status_code == 404


def test_delete_task_qa_item(client, mock_task):
    task_table.get_task_by_id = MagicMock(return_value=mock_task)
    TokenVerifier.verify = mock_verify_dev
    qa_item_table.delete_qa_item_by_id = MagicMock(return_value=True)

    response = client.delete(f"/task/{mock_task.id}/qa/qa-1")

    assert response.status_code == 200
    assert response.json() == {"id": "qa-1", "status": "deleted"}


def test_delete_task_qa_item_not_found(client, mock_task):
    task_table.get_task_by_id = MagicMock(return_value=mock_task)
    TokenVerifier.verify = mock_verify_dev
    qa_item_table.delete_qa_item_by_id = MagicMock(return_value=False)

    response = client.delete(f"/task/{mock_task.id}/qa/missing")

    assert response.status_code == 404


def test_create_task_entities_saves_the_chunk(internal_client):
    task_table.get_task_by_id = MagicMock(return_value=SimpleNamespace(id="123"))
    entity_table.save_chunk_entities = MagicMock()

    response = internal_client.post(
        "/task/123/entities",
        json={
            "chunk_index": 0,
            "entities": [{"type": "PERSON", "text": "Alice", "contexts": [], "pages": [1]}],
            "relationships": [{"source_index": 0, "target_index": 0, "relationship_type": "SELF", "description": "d"}],
        },
    )

    assert response.status_code == 201
    args, kwargs = entity_table.save_chunk_entities.call_args
    assert kwargs["task_id"] == "123"
    assert kwargs["chunk_index"] == 0
    assert kwargs["entities"][0].text == "Alice"
    assert kwargs["relationships"][0].relationship_type == "SELF"


def test_create_task_entities_requires_internal_auth(client):
    response = client.post("/task/123/entities", json={"chunk_index": 0, "entities": []})
    assert response.status_code == 401


def test_delete_task_entity(client, mock_task):
    task_table.get_task_by_id = MagicMock(return_value=mock_task)
    TokenVerifier.verify = mock_verify_dev
    entity_table.delete_entity_by_id = MagicMock(return_value=True)

    response = client.delete(f"/task/{mock_task.id}/entities/ent-1")

    assert response.status_code == 200
    assert response.json() == {"id": "ent-1", "status": "deleted"}


def test_create_task_global_relationships_saves(internal_client):
    task_table.get_task_by_id = MagicMock(return_value=SimpleNamespace(id="123"))
    entity_table.save_global_relationships = MagicMock()

    response = internal_client.post(
        "/task/123/relationships/global",
        json={
            "entity_ids_in_order": ["ent-1", "ent-2"],
            "relationships": [{"source_index": 0, "target_index": 1, "relationship_type": "WORKS_AT", "description": "d"}],
        },
    )

    assert response.status_code == 201
    args, kwargs = entity_table.save_global_relationships.call_args
    assert kwargs["task_id"] == "123"
    assert kwargs["entity_ids_in_order"] == ["ent-1", "ent-2"]
    assert kwargs["relationships"][0].relationship_type == "WORKS_AT"


def test_create_task_global_relationships_requires_internal_auth(client):
    response = client.post("/task/123/relationships/global", json={"entity_ids_in_order": [], "relationships": []})
    assert response.status_code == 401


def test_delete_task_relationship(client, mock_task):
    task_table.get_task_by_id = MagicMock(return_value=mock_task)
    TokenVerifier.verify = mock_verify_dev
    entity_table.delete_relationship_by_id = MagicMock(return_value=True)

    response = client.delete(f"/task/{mock_task.id}/relationships/rel-1")

    assert response.status_code == 200
    assert response.json() == {"id": "rel-1", "status": "deleted"}
