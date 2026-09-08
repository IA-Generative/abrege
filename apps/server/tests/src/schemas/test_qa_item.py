import uuid

from src.schemas.qa_item import QAItemTable
from src.schemas.result import QAItem


def _task_id() -> str:
    return f"task-{uuid.uuid4()}"


def test_save_chunk_qa_items_persists_rows():
    table = QAItemTable()
    task_id = _task_id()

    table.save_chunk_qa_items(
        task_id=task_id,
        chunk_index=0,
        qa_items=[
            QAItem(page=1, source_text="Le ciel est bleu.", question="De quelle couleur est le ciel ?", answer="Bleu"),
            QAItem(page=1, source_text="Le ciel est bleu.", question="Qu'est-ce qui est bleu ?", answer="Le ciel"),
        ],
    )

    rows = table.get_qa_items_by_task(task_id)

    assert len(rows) == 2
    assert {row.question for row in rows} == {"De quelle couleur est le ciel ?", "Qu'est-ce qui est bleu ?"}
    assert all(row.task_id == task_id for row in rows)
    assert all(row.chunk_index == 0 for row in rows)
    assert all(row.page == 1 for row in rows)


def test_save_chunk_qa_items_is_idempotent_per_chunk_on_retry():
    table = QAItemTable()
    task_id = _task_id()

    table.save_chunk_qa_items(
        task_id=task_id,
        chunk_index=0,
        qa_items=[QAItem(page=1, source_text="src", question="Q1", answer="A1")],
    )
    # Simulate a Celery retry of the same chunk with a (possibly different) LLM output.
    table.save_chunk_qa_items(
        task_id=task_id,
        chunk_index=0,
        qa_items=[QAItem(page=1, source_text="src", question="Q1-bis", answer="A1-bis")],
    )

    rows = table.get_qa_items_by_task(task_id)

    assert len(rows) == 1
    assert rows[0].question == "Q1-bis"


def test_save_chunk_qa_items_keeps_other_chunks_untouched():
    table = QAItemTable()
    task_id = _task_id()

    table.save_chunk_qa_items(task_id=task_id, chunk_index=0, qa_items=[QAItem(page=1, source_text="a", question="Q0", answer="A0")])
    table.save_chunk_qa_items(task_id=task_id, chunk_index=1, qa_items=[QAItem(page=2, source_text="b", question="Q1", answer="A1")])

    # Retrying chunk 0 must not delete chunk 1's rows.
    table.save_chunk_qa_items(task_id=task_id, chunk_index=0, qa_items=[])

    rows = table.get_qa_items_by_task(task_id)

    assert len(rows) == 1
    assert rows[0].chunk_index == 1
    assert rows[0].question == "Q1"


def test_get_qa_items_by_task_returns_empty_list_when_none():
    table = QAItemTable()
    assert table.get_qa_items_by_task(_task_id()) == []
