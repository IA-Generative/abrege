import json
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from abrege_service.main import classify_topics, internal_api_client, llm, topic_runnable
from abrege_service.models.summary.topic_chain import TopicClassificationOutput, TopicOutput
from src.schemas.task import TaskForm, TaskStatus, task_table


def _task_id() -> str:
    return f"task-{uuid.uuid4()}"


def _make_task() -> str:
    task = task_table.insert_new_task(user_id="test", form_data=TaskForm(type="summary", status=TaskStatus.COMPLETED.value))
    return task.id


def test_classify_topics_saves_through_the_internal_api(monkeypatch: pytest.MonkeyPatch):
    task_id = _task_id()
    monkeypatch.setattr(
        topic_runnable,
        "ainvoke",
        AsyncMock(
            return_value=TopicClassificationOutput(
                topics=[
                    TopicOutput(topic="finance", confidence=0.9, explanation="Résultats financiers en hausse."),
                    TopicOutput(topic="ressources humaines", confidence=0.4, explanation="Mention des effectifs."),
                ]
            )
        ),
    )
    monkeypatch.setattr(internal_api_client, "save_topics", MagicMock())

    payload = json.dumps({"task_id": task_id, "summary": "Résumé du document.", "language": "French"})
    classify_topics.apply(args=[payload]).get()

    topic_runnable.ainvoke.assert_called_once_with({"text": "Résumé du document.", "language": "French"})
    internal_api_client.save_topics.assert_called_once_with(
        task_id=task_id,
        topics=[
            {"topic": "finance", "confidence": 0.9, "explanation": "Résultats financiers en hausse."},
            {"topic": "ressources humaines", "confidence": 0.4, "explanation": "Mention des effectifs."},
        ],
        model_name=llm.model_name,
    )


def test_classify_topics_does_not_swallow_internal_api_errors(monkeypatch: pytest.MonkeyPatch):
    task_id = _task_id()
    monkeypatch.setattr(topic_runnable, "ainvoke", AsyncMock(return_value=TopicClassificationOutput(topics=[])))
    monkeypatch.setattr(internal_api_client, "save_topics", MagicMock(side_effect=RuntimeError("api down")))

    payload = json.dumps({"task_id": task_id, "summary": "x", "language": "French"})

    with pytest.raises(RuntimeError):
        classify_topics.apply(args=[payload]).get()


def test_classify_topics_marks_topics_status_completed(monkeypatch: pytest.MonkeyPatch):
    task_id = _make_task()
    monkeypatch.setattr(topic_runnable, "ainvoke", AsyncMock(return_value=TopicClassificationOutput(topics=[])))
    monkeypatch.setattr(internal_api_client, "save_topics", MagicMock())

    classify_topics.apply(args=[json.dumps({"task_id": task_id, "summary": "x", "language": "French"})]).get()

    assert task_table.get_task_by_id(task_id).topics_status == "completed"


def test_classify_topics_marks_topics_status_failed_on_error(monkeypatch: pytest.MonkeyPatch):
    task_id = _make_task()
    monkeypatch.setattr(topic_runnable, "ainvoke", AsyncMock(return_value=TopicClassificationOutput(topics=[])))
    monkeypatch.setattr(internal_api_client, "save_topics", MagicMock(side_effect=RuntimeError("api down")))

    with pytest.raises(RuntimeError):
        classify_topics.apply(args=[json.dumps({"task_id": task_id, "summary": "x", "language": "French"})]).get()

    assert task_table.get_task_by_id(task_id).topics_status == "failed"
