import uuid

from src.schemas.result import TopicModel
from src.schemas.topic import TopicTable


def _task_id() -> str:
    return f"task-{uuid.uuid4()}"


def test_save_topics_persists_rows():
    table = TopicTable()
    task_id = _task_id()

    table.save_topics(
        task_id=task_id,
        topics=[
            TopicModel(topic="finance", confidence=0.9, explanation="Le document parle de résultats financiers."),
            TopicModel(topic="ressources humaines", confidence=0.4, explanation="Mention des effectifs."),
        ],
        model_name="gpt-4",
    )

    rows = table.get_topics_by_task(task_id)

    assert len(rows) == 2
    assert {r.topic for r in rows} == {"finance", "ressources humaines"}
    assert all(r.task_id == task_id for r in rows)
    assert all(r.model_name == "gpt-4" for r in rows)
    # ordered by confidence desc
    assert rows[0].topic == "finance"


def test_save_topics_replaces_previous_classification_on_retry():
    table = TopicTable()
    task_id = _task_id()

    table.save_topics(task_id=task_id, topics=[TopicModel(topic="finance", confidence=0.9, explanation="e1")])
    table.save_topics(task_id=task_id, topics=[TopicModel(topic="santé", confidence=0.7, explanation="e2")])

    rows = table.get_topics_by_task(task_id)

    assert len(rows) == 1
    assert rows[0].topic == "santé"


def test_get_topics_by_task_paginated_slices_and_counts():
    table = TopicTable()
    task_id = _task_id()
    table.save_topics(
        task_id=task_id,
        topics=[TopicModel(topic=f"topic-{i}", confidence=i / 10, explanation="e") for i in range(5)],
    )

    assert table.count_topics_by_task(task_id) == 5

    page_1 = table.get_topics_by_task_paginated(task_id, page=1, page_size=2)
    page_2 = table.get_topics_by_task_paginated(task_id, page=2, page_size=2)
    page_3 = table.get_topics_by_task_paginated(task_id, page=3, page_size=2)

    # ordered by confidence desc: topic-4 (.4), topic-3 (.3), topic-2 (.2), topic-1 (.1), topic-0 (0)
    assert [r.topic for r in page_1] == ["topic-4", "topic-3"]
    assert [r.topic for r in page_2] == ["topic-2", "topic-1"]
    assert [r.topic for r in page_3] == ["topic-0"]


def test_get_topic_by_id_and_delete():
    table = TopicTable()
    task_id = _task_id()
    table.save_topics(task_id=task_id, topics=[TopicModel(topic="finance", confidence=0.9, explanation="e")])
    row = table.get_topics_by_task(task_id)[0]

    fetched = table.get_topic_by_id(task_id, row.id)
    assert fetched is not None
    assert fetched.topic == "finance"

    assert table.delete_topic_by_id(task_id, row.id) is True
    assert table.get_topic_by_id(task_id, row.id) is None
    assert table.delete_topic_by_id(task_id, row.id) is False


def test_get_topics_by_task_returns_empty_list_when_none():
    table = TopicTable()
    assert table.get_topics_by_task(_task_id()) == []
    assert table.count_topics_by_task(_task_id()) == 0
