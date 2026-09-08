import uuid

from src.schemas.chunk import ChunkTable


def _task_id() -> str:
    return f"task-{uuid.uuid4()}"


def test_save_chunk_group_persists_chunks_in_order():
    table = ChunkTable()
    task_id = _task_id()

    table.save_chunk_group(
        task_id=task_id,
        chunk_index=0,
        page=1,
        chunks=["Premier sujet.", "Deuxième sujet."],
        model_name="gpt-4",
    )

    rows = table.get_chunks_by_task_paginated(task_id, page=1, page_size=20)

    assert len(rows) == 2
    assert [r.text for r in rows] == ["Premier sujet.", "Deuxième sujet."]
    assert [r.position for r in rows] == [0, 1]
    assert all(r.chunk_index == 0 for r in rows)
    assert all(r.page == 1 for r in rows)
    assert all(r.model_name == "gpt-4" for r in rows)


def test_save_chunk_group_is_idempotent_per_window_on_retry():
    table = ChunkTable()
    task_id = _task_id()

    table.save_chunk_group(task_id=task_id, chunk_index=0, page=1, chunks=["A", "B"], model_name="gpt-4")
    table.save_chunk_group(task_id=task_id, chunk_index=0, page=1, chunks=["A-bis"], model_name="gpt-4")

    rows = table.get_chunks_by_task_paginated(task_id, page=1, page_size=20)

    assert len(rows) == 1
    assert rows[0].text == "A-bis"


def test_save_chunk_group_keeps_other_windows_untouched():
    table = ChunkTable()
    task_id = _task_id()

    table.save_chunk_group(task_id=task_id, chunk_index=0, page=1, chunks=["A"], model_name="gpt-4")
    table.save_chunk_group(task_id=task_id, chunk_index=1, page=2, chunks=["B"], model_name="gpt-4")

    table.save_chunk_group(task_id=task_id, chunk_index=0, page=1, chunks=[], model_name="gpt-4")

    rows = table.get_chunks_by_task_paginated(task_id, page=1, page_size=20)

    assert len(rows) == 1
    assert rows[0].chunk_index == 1
    assert rows[0].text == "B"


def test_get_chunks_by_task_paginated_slices_and_counts():
    table = ChunkTable()
    task_id = _task_id()
    for i in range(5):
        table.save_chunk_group(task_id=task_id, chunk_index=i, page=i, chunks=[f"chunk-{i}"], model_name="gpt-4")

    assert table.count_chunks_by_task(task_id) == 5

    page_1 = table.get_chunks_by_task_paginated(task_id, page=1, page_size=2)
    page_2 = table.get_chunks_by_task_paginated(task_id, page=2, page_size=2)
    page_3 = table.get_chunks_by_task_paginated(task_id, page=3, page_size=2)

    assert [r.text for r in page_1] == ["chunk-0", "chunk-1"]
    assert [r.text for r in page_2] == ["chunk-2", "chunk-3"]
    assert [r.text for r in page_3] == ["chunk-4"]


def test_get_chunk_by_id_and_delete():
    table = ChunkTable()
    task_id = _task_id()
    table.save_chunk_group(task_id=task_id, chunk_index=0, page=1, chunks=["A"], model_name="gpt-4")
    row = table.get_chunks_by_task_paginated(task_id, page=1, page_size=20)[0]

    fetched = table.get_chunk_by_id(task_id, row.id)
    assert fetched is not None
    assert fetched.text == "A"

    assert table.delete_chunk_by_id(task_id, row.id) is True
    assert table.get_chunk_by_id(task_id, row.id) is None
    assert table.delete_chunk_by_id(task_id, row.id) is False


def test_get_chunks_by_task_returns_empty_when_none():
    table = ChunkTable()
    assert table.get_chunks_by_task_paginated(_task_id(), page=1, page_size=20) == []
    assert table.count_chunks_by_task(_task_id()) == 0
