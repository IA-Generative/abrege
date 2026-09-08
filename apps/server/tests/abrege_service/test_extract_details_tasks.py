import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

import abrege_service.main as main
from abrege_service.main import (
    compute_global_relationships,
    extract_chunk_details,
    extract_task_details,
    internal_api_client,
    llm,
    summary_service,
)
from abrege_service.models.summary.chunk_chain import ChunkingOutput
from abrege_service.models.summary.entity_chain import ChunkEntitiesOutput, ChunkEntityOutput, ChunkRelationshipOutput, GlobalRelationshipsOutput
from abrege_service.models.summary.qa_chain import QAItemOutput, QAOutput
from src.clients import celery_app, redis_client
from src.schemas.entity import entity_table
from src.schemas.parameters import SummaryParameters
from src.schemas.result import EntityModel, ResultModel
from src.schemas.task import TaskForm, TaskStatus, task_table


def _task_id() -> str:
    task = task_table.insert_new_task(user_id="test", form_data=TaskForm(type="summary", status=TaskStatus.COMPLETED.value))
    return task.id


def _mock_extraction_runnables(monkeypatch: pytest.MonkeyPatch, qa_items=None, entities=None, relationships=None, chunks=None):
    monkeypatch.setattr(main, "qa_runnable", SimpleNamespace(ainvoke=AsyncMock(return_value=QAOutput(items=qa_items or []))))
    monkeypatch.setattr(
        main,
        "entity_runnable",
        SimpleNamespace(ainvoke=AsyncMock(return_value=ChunkEntitiesOutput(entities=entities or [], relationships=relationships or []))),
    )
    monkeypatch.setattr(
        main, "chunk_runnable", SimpleNamespace(ainvoke=AsyncMock(return_value=ChunkingOutput(chunks=chunks if chunks is not None else ["x"])))
    )


def test_extract_chunk_details_saves_qa_entities_and_chunks_through_the_internal_api(monkeypatch: pytest.MonkeyPatch):
    task_id = _task_id()
    _mock_extraction_runnables(
        monkeypatch,
        qa_items=[QAItemOutput(question="Q1", answer="A1")],
        entities=[ChunkEntityOutput(type="PERSON", text="Alice", contexts=["ctx"])],
        chunks=["Alice dit bonjour."],
    )
    monkeypatch.setattr(redis_client, "decr", lambda key: 1)  # not the last chunk
    monkeypatch.setattr(internal_api_client, "save_chunk_qa_items", MagicMock())
    monkeypatch.setattr(internal_api_client, "save_chunk_entities", MagicMock())
    monkeypatch.setattr(internal_api_client, "save_chunks", MagicMock())

    payload = json.dumps(
        {
            "task_id": task_id,
            "chunk_index": 0,
            "page": 2,
            "text": "Alice dit bonjour.",
            "language": "French",
            "qa_per_chunk": 3,
        }
    )

    extract_chunk_details.apply(args=[payload]).get()

    internal_api_client.save_chunk_qa_items.assert_called_once_with(
        task_id=task_id,
        chunk_index=0,
        qa_items=[{"page": 2, "source_text": "Alice dit bonjour.", "question": "Q1", "answer": "A1"}],
        model_name=llm.model_name,
    )
    internal_api_client.save_chunk_entities.assert_called_once_with(
        task_id=task_id,
        chunk_index=0,
        entities=[{"type": "PERSON", "text": "Alice", "contexts": ["ctx"], "pages": [2]}],
        relationships=[],
        model_name=llm.model_name,
    )
    internal_api_client.save_chunks.assert_called_once_with(
        task_id=task_id,
        chunk_index=0,
        page=2,
        chunks=["Alice dit bonjour."],
        model_name=llm.model_name,
    )


def test_extract_chunk_details_falls_back_to_original_text_when_no_chunks_returned(monkeypatch: pytest.MonkeyPatch):
    task_id = _task_id()
    _mock_extraction_runnables(monkeypatch, chunks=[])
    monkeypatch.setattr(redis_client, "decr", lambda key: 1)
    monkeypatch.setattr(internal_api_client, "save_chunk_qa_items", MagicMock())
    monkeypatch.setattr(internal_api_client, "save_chunk_entities", MagicMock())
    monkeypatch.setattr(internal_api_client, "save_chunks", MagicMock())

    payload = json.dumps({"task_id": task_id, "chunk_index": 0, "page": None, "text": "texte original", "language": "French", "qa_per_chunk": 3})
    extract_chunk_details.apply(args=[payload]).get()

    internal_api_client.save_chunks.assert_called_once_with(
        task_id=task_id, chunk_index=0, page=None, chunks=["texte original"], model_name=llm.model_name
    )


def test_extract_chunk_details_does_not_swallow_internal_api_errors(monkeypatch: pytest.MonkeyPatch):
    task_id = _task_id()
    _mock_extraction_runnables(monkeypatch)
    monkeypatch.setattr(internal_api_client, "save_chunk_qa_items", MagicMock(side_effect=RuntimeError("api down")))

    payload = json.dumps({"task_id": task_id, "chunk_index": 0, "page": None, "text": "x", "language": "French", "qa_per_chunk": 3})

    with pytest.raises(RuntimeError):
        extract_chunk_details.apply(args=[payload]).get()


def test_extract_chunk_details_triggers_global_relationships_on_last_chunk(monkeypatch: pytest.MonkeyPatch):
    task_id = _task_id()
    _mock_extraction_runnables(monkeypatch)
    monkeypatch.setattr(internal_api_client, "save_chunk_qa_items", MagicMock())
    monkeypatch.setattr(internal_api_client, "save_chunk_entities", MagicMock())
    monkeypatch.setattr(internal_api_client, "save_chunks", MagicMock())
    monkeypatch.setattr(redis_client, "decr", lambda key: 0)  # last chunk

    deleted_keys = []
    monkeypatch.setattr(redis_client, "delete", lambda key: deleted_keys.append(key))

    sent = []
    monkeypatch.setattr(celery_app, "send_task", lambda name, args, task_id=None: sent.append((name, task_id)))

    payload = json.dumps({"task_id": task_id, "chunk_index": 0, "page": None, "text": "x", "language": "French", "qa_per_chunk": 3})
    extract_chunk_details.apply(args=[payload]).get()

    assert deleted_keys == [f"chunk_pending:{task_id}"]
    assert sent == [("worker.tasks.compute_global_relationships", f"{task_id}:global-relationships")]


def test_compute_global_relationships_saves_through_the_internal_api(monkeypatch: pytest.MonkeyPatch):
    task_id = _task_id()
    # Entity reads still go straight to the DB (only writes go through the internal API).
    entity_table.save_chunk_entities(
        task_id=task_id,
        chunk_index=0,
        entities=[EntityModel(type="PERSON", text="Alice", contexts=[], pages=[1])],
        relationships=[],
    )
    entity_table.save_chunk_entities(
        task_id=task_id,
        chunk_index=1,
        entities=[EntityModel(type="ORGANIZATION", text="Acme", contexts=[], pages=[2])],
        relationships=[],
    )
    entities = entity_table.get_entities_by_task(task_id)
    entity_by_text = {e.text: e.id for e in entities}

    monkeypatch.setattr(
        main,
        "global_relationship_runnable",
        SimpleNamespace(
            ainvoke=AsyncMock(
                return_value=GlobalRelationshipsOutput(
                    relationships=[ChunkRelationshipOutput(source_index=0, target_index=1, relationship_type="WORKS_AT", description="link")]
                )
            )
        ),
    )
    monkeypatch.setattr(internal_api_client, "save_global_relationships", MagicMock())

    compute_global_relationships.apply(args=[json.dumps({"task_id": task_id})]).get()

    internal_api_client.save_global_relationships.assert_called_once_with(
        task_id=task_id,
        entity_ids_in_order=[entity_by_text["Alice"], entity_by_text["Acme"]],
        relationships=[{"source_index": 0, "target_index": 1, "relationship_type": "WORKS_AT", "description": "link"}],
        model_name=llm.model_name,
    )


def test_compute_global_relationships_skips_when_fewer_than_two_entities(monkeypatch: pytest.MonkeyPatch):
    task_id = _task_id()
    mock_ainvoke = AsyncMock()
    monkeypatch.setattr(main, "global_relationship_runnable", SimpleNamespace(ainvoke=mock_ainvoke))
    monkeypatch.setattr(internal_api_client, "save_global_relationships", MagicMock())

    compute_global_relationships.apply(args=[json.dumps({"task_id": task_id})]).get()

    mock_ainvoke.assert_not_called()
    internal_api_client.save_global_relationships.assert_not_called()


def test_extract_task_details_dispatches_chunks_for_a_completed_task(monkeypatch: pytest.MonkeyPatch):
    task = task_table.insert_new_task(
        user_id="test",
        form_data=TaskForm(
            type="summary",
            status=TaskStatus.COMPLETED.value,
            parameters=SummaryParameters(extract_qa=False, qa_per_chunk=3, language="French"),
            output=ResultModel(
                type="flat",
                created_at=0,
                model_name="mock",
                model_version="mock",
                texts_found=["Un texte assez court pour tenir dans un seul chunk."],
            ),
        ),
    )

    dispatched = []
    monkeypatch.setattr(
        summary_service,
        "dispatch_all_chunks",
        lambda task_id, texts, language, qa_per_chunk: dispatched.append((task_id, texts, language, qa_per_chunk)),
    )

    extract_task_details.apply(args=[task.id]).get()

    assert len(dispatched) == 1
    dispatched_task_id, dispatched_texts, dispatched_language, dispatched_qa_per_chunk = dispatched[0]
    assert dispatched_task_id == task.id
    assert dispatched_language == "French"
    assert dispatched_qa_per_chunk == 3
    assert len(dispatched_texts) >= 1


def test_extract_task_details_noop_when_task_has_no_source_text():
    task = task_table.insert_new_task(
        user_id="test",
        form_data=TaskForm(type="summary", status=TaskStatus.COMPLETED.value),
    )

    # Must not raise even though task.output is None.
    extract_task_details.apply(args=[task.id]).get()


# ---------------------------------------------------------------------------
# Status tracking on the parent Task — how the frontend knows a side extraction is done
# ---------------------------------------------------------------------------


def test_extract_chunk_details_marks_qa_entities_completed_and_relationships_pending_on_last_chunk(monkeypatch: pytest.MonkeyPatch):
    task_id = _task_id()
    _mock_extraction_runnables(monkeypatch)
    monkeypatch.setattr(internal_api_client, "save_chunk_qa_items", MagicMock())
    monkeypatch.setattr(internal_api_client, "save_chunk_entities", MagicMock())
    monkeypatch.setattr(internal_api_client, "save_chunks", MagicMock())
    monkeypatch.setattr(redis_client, "decr", lambda key: 0)  # last chunk
    monkeypatch.setattr(redis_client, "delete", lambda key: None)
    monkeypatch.setattr(celery_app, "send_task", lambda name, args, task_id=None: None)

    payload = json.dumps({"task_id": task_id, "chunk_index": 0, "page": None, "text": "x", "language": "French", "qa_per_chunk": 3})
    extract_chunk_details.apply(args=[payload]).get()

    updated = task_table.get_task_by_id(task_id)
    assert updated.qa_entities_status == "completed"
    assert updated.relationships_status == "pending"


def test_extract_chunk_details_leaves_qa_entities_in_progress_when_not_last_chunk(monkeypatch: pytest.MonkeyPatch):
    task_id = _task_id()
    _mock_extraction_runnables(monkeypatch)
    monkeypatch.setattr(internal_api_client, "save_chunk_qa_items", MagicMock())
    monkeypatch.setattr(internal_api_client, "save_chunk_entities", MagicMock())
    monkeypatch.setattr(internal_api_client, "save_chunks", MagicMock())
    monkeypatch.setattr(redis_client, "decr", lambda key: 1)  # not the last chunk

    payload = json.dumps({"task_id": task_id, "chunk_index": 0, "page": None, "text": "x", "language": "French", "qa_per_chunk": 3})
    extract_chunk_details.apply(args=[payload]).get()

    updated = task_table.get_task_by_id(task_id)
    assert updated.qa_entities_status is None
    assert updated.relationships_status is None


def test_extract_chunk_details_marks_qa_entities_failed_on_error(monkeypatch: pytest.MonkeyPatch):
    task_id = _task_id()
    _mock_extraction_runnables(monkeypatch)
    monkeypatch.setattr(internal_api_client, "save_chunk_qa_items", MagicMock(side_effect=RuntimeError("api down")))

    payload = json.dumps({"task_id": task_id, "chunk_index": 0, "page": None, "text": "x", "language": "French", "qa_per_chunk": 3})
    with pytest.raises(RuntimeError):
        extract_chunk_details.apply(args=[payload]).get()

    updated = task_table.get_task_by_id(task_id)
    assert updated.qa_entities_status == "failed"


def test_compute_global_relationships_marks_relationships_completed(monkeypatch: pytest.MonkeyPatch):
    task_id = _task_id()
    entity_table.save_chunk_entities(
        task_id=task_id,
        chunk_index=0,
        entities=[EntityModel(type="PERSON", text="Alice", contexts=[], pages=[1]), EntityModel(type="ORGANIZATION", text="Acme", contexts=[], pages=[1])],
        relationships=[],
    )
    monkeypatch.setattr(
        main, "global_relationship_runnable", SimpleNamespace(ainvoke=AsyncMock(return_value=GlobalRelationshipsOutput(relationships=[])))
    )
    monkeypatch.setattr(internal_api_client, "save_global_relationships", MagicMock())

    compute_global_relationships.apply(args=[json.dumps({"task_id": task_id})]).get()

    assert task_table.get_task_by_id(task_id).relationships_status == "completed"


def test_compute_global_relationships_marks_relationships_completed_when_skipped(monkeypatch: pytest.MonkeyPatch):
    task_id = _task_id()  # no entities saved: fewer than two -> early return

    compute_global_relationships.apply(args=[json.dumps({"task_id": task_id})]).get()

    assert task_table.get_task_by_id(task_id).relationships_status == "completed"


def test_compute_global_relationships_marks_relationships_failed_on_error(monkeypatch: pytest.MonkeyPatch):
    task_id = _task_id()
    entity_table.save_chunk_entities(
        task_id=task_id,
        chunk_index=0,
        entities=[EntityModel(type="PERSON", text="Alice", contexts=[], pages=[1]), EntityModel(type="ORGANIZATION", text="Acme", contexts=[], pages=[1])],
        relationships=[],
    )
    monkeypatch.setattr(main, "global_relationship_runnable", SimpleNamespace(ainvoke=AsyncMock(side_effect=RuntimeError("llm down"))))

    with pytest.raises(RuntimeError):
        compute_global_relationships.apply(args=[json.dumps({"task_id": task_id})]).get()

    assert task_table.get_task_by_id(task_id).relationships_status == "failed"


def test_extract_task_details_marks_qa_entities_in_progress(monkeypatch: pytest.MonkeyPatch):
    task = task_table.insert_new_task(
        user_id="test",
        form_data=TaskForm(
            type="summary",
            status=TaskStatus.COMPLETED.value,
            parameters=SummaryParameters(extract_qa=False, qa_per_chunk=3, language="French"),
            output=ResultModel(
                type="flat", created_at=0, model_name="mock", model_version="mock",
                texts_found=["Un texte assez court pour tenir dans un seul chunk."],
            ),
        ),
    )
    monkeypatch.setattr(summary_service, "dispatch_all_chunks", lambda **kwargs: None)

    extract_task_details.apply(args=[task.id]).get()

    assert task_table.get_task_by_id(task.id).qa_entities_status == "in_progress"
