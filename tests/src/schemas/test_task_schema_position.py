import pytest
from datetime import datetime
from src.schemas.task import Task, TaskStatus
from sqlalchemy import delete
from sqlalchemy.exc import SQLAlchemyError
from src.schemas.task import task_table, TaskForm, get_db
import time


@pytest.fixture(autouse=True)
def clear_task_table_fixture():
    """Vide la table Task après chaque test."""
    yield  # laisse exécuter le test
    with get_db() as db:
        try:
            db.execute(delete(Task))
            db.commit()
        except SQLAlchemyError:
            db.rollback()


def test_task_not_found():
    assert task_table.get_position_in_queue("non_existent_id") is None


def test_task_not_in_queue():
    now = int(datetime.now().timestamp())
    task1 = task_table.insert_new_task(
        user_id="t1",
        form_data=TaskForm(
            type="ocr",
            user_id="t1",
            percentage=0.0,
            status=TaskStatus.COMPLETED,
            created_at=now - 30,
        ),
    )

    assert task_table.get_position_in_queue(task1.id) is None


def test_task_in_queue_position_zero():
    now = int(datetime.now().timestamp())
    task1 = task_table.insert_new_task(
        user_id="t1",
        form_data=TaskForm(
            type="ocr",
            user_id="t1",
            percentage=0.0,
            status=TaskStatus.QUEUED,
            created_at=now - 30,
        ),
    )

    assert task_table.get_position_in_queue(task1.id) == 0


def test_task_in_queue_position_two():
    now = int(datetime.now().timestamp())
    task1 = task_table.insert_new_task(
        user_id="t1",
        form_data=TaskForm(
            type="ocr",
            user_id="t1",
            percentage=0.0,
            status=TaskStatus.QUEUED,
            created_at=now - 30,
        ),
    )
    time.sleep(2)
    task2 = task_table.insert_new_task(
        user_id="t2",
        form_data=TaskForm(
            type="ocr",
            user_id="t2",
            percentage=0.0,
            status=TaskStatus.QUEUED,
            created_at=now - 20,
        ),
    )
    time.sleep(2)
    task3 = task_table.insert_new_task(
        user_id="t3",
        form_data=TaskForm(
            type="ocr",
            user_id="t3",
            percentage=0.0,
            status=TaskStatus.QUEUED,
            created_at=now,
        ),
    )
    task3_position = task_table.get_position_in_queue(task3.id)
    task2_position = task_table.get_position_in_queue(task2.id)
    task1_position = task_table.get_position_in_queue(task1.id)
    print(task1_position, task2_position, task3_position)
    print(79 * "*")

    assert task3_position == 2
    assert task2_position == task3_position - 1

    assert task1_position == task2_position - 1
