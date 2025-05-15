from src.schemas.task import (
    TaskTable,
    TaskForm,
    TaskUpdateForm,
    TaskStatus,
)
from src.schemas.content import URLModel, DocumentModel, TextModel
from src.schemas.result import SummaryModel


def test_insert_new_task():
    task_table = TaskTable()
    user_id = "user123"
    form_data = TaskForm(
        type="classification",
        status=TaskStatus.QUEUED.value,
        input=None,
        output=None,
        extras={"source": "test"},
    )

    result = task_table.insert_new_task(user_id=user_id, form_data=form_data)

    assert result is not None
    assert result.user_id == user_id
    assert result.type == "classification"
    assert result.status == TaskStatus.QUEUED.value
    assert result.extras["source"] == "test"
    assert isinstance(result.created_at, int)
    assert isinstance(result.updated_at, int)


def test_insert_new_task_content():
    task_table = TaskTable()
    user_id = "user123"

    content_model_url = URLModel(url="https://lll", created_at=0, extras=None)
    content_model_doc = DocumentModel(
        file_path="/add/dsdqs.txt",
        raw_filename="dada",
        content_type="",
        created_at=0,
        size=0,
        ext="",
        extras=None,
    )
    content_model_text = TextModel(text="/add/dsdqs.txt", created_at=0, extras=None)

    result_summary = SummaryModel(
        summary="bonjour",
        word_count=1,
        created_at=0,
        model_name="summe",
        model_version="1",
        percentage=0.0,
        extras=None,
    )
    for content_model in [content_model_doc, content_model_url, content_model_text]:
        for result_tmp in [result_summary, None]:
            form_data = TaskForm(
                type="classification",
                status=TaskStatus.QUEUED.value,
                input=content_model,
                output=result_tmp,
                extras={"source": "test"},
            )

            result = task_table.insert_new_task(user_id=user_id, form_data=form_data)

            assert result is not None
            assert result.user_id == user_id
            assert result.type == "classification"
            assert result.status == TaskStatus.QUEUED.value
            assert result.extras["source"] == "test"
            assert isinstance(result.created_at, int)
            assert isinstance(result.updated_at, int)
            assert result.input == content_model
            assert result.output == result_tmp


def test_update_task():
    table = TaskTable()

    new_task = table.insert_new_task(
        user_id="user456",
        form_data=TaskForm(
            type="summary",
            status=TaskStatus.QUEUED.value,
            extras={"initial": True},
        ),
    )

    assert new_task is not None

    update_form = TaskUpdateForm(status="done", extras={"updated": True})

    updated = table.update_task(task_id=new_task.id, form_data=update_form)

    assert updated is not None
    assert updated.id == new_task.id
    assert updated.status == "done"
    assert updated.extras == {"updated": True}

    not_found_updated = table.update_task(task_id="zzz", form_data=update_form)
    assert not_found_updated is None


def test_get_task_by_id():
    table = TaskTable()

    # Step 1: Insert a task
    task = table.insert_new_task(
        user_id="user789",
        form_data=TaskForm(
            type="detection",
            status=TaskStatus.QUEUED.value,
            percentage=0.0,
            extras={"test": True},
        ),
    )

    assert task is not None

    # Step 2: Retrieve it
    retrieved = table.get_task_by_id(task.id)

    # Step 3: Assertions
    assert retrieved is not None
    assert retrieved.id == task.id
    assert retrieved.type == "detection"
    assert retrieved.status == TaskStatus.QUEUED.value


def test_get_task_by_invalid_id():
    table = TaskTable()
    result = table.get_task_by_id("non-existent-id")
    assert result is None


def test_delete_task_by_id():
    table = TaskTable()

    # Step 1: Create a task
    task = table.insert_new_task(
        user_id="user123",
        form_data=TaskForm(
            type="task_type",
            status=TaskStatus.QUEUED.value,
            extras={"key": "value"},
        ),
    )

    assert task is not None

    # Step 2: Delete the task by id
    deleted_task = table.delete_task_by_id(task.id)

    # Step 3: Assertions
    assert deleted_task is not None
    assert deleted_task.id == task.id  # Ensure it's the same task

    # Step 4: Check that the task is deleted (it should return None now)
    task_after_deletion = table.get_task_by_id(task.id)
    assert task_after_deletion is None

    not_found_deleted_task = table.delete_task_by_id("task.id")
    assert not_found_deleted_task is None


def test_get_tasks_by_user_id_with_pagination():
    table = TaskTable()

    # Step 1: Insert 15 tasks for user123
    for i in range(15):
        table.insert_new_task(
            user_id="user123",
            form_data=TaskForm(
                type=f"task_type_{i}",
                status=TaskStatus.QUEUED.value,
                extras={"key": f"value_{i}"},
            ),
        )

    # Step 2: Retrieve first page with 5 tasks per page
    tasks_page_1 = table.get_tasks_by_user_id(user_id="user123", page=1, page_size=5)
    assert tasks_page_1 is not None
    assert len(tasks_page_1) == 5  # First page should contain 5 tasks

    # Step 3: Retrieve second page with 5 tasks per page
    tasks_page_2 = table.get_tasks_by_user_id(user_id="user123", page=2, page_size=5)
    assert tasks_page_2 is not None
    assert len(tasks_page_2) == 5  # Second page should also contain 5 tasks

    # Step 4: Retrieve third page with 5 tasks per page (which should be the last page)
    tasks_page_3 = table.get_tasks_by_user_id(user_id="user123", page=3, page_size=5)
    assert tasks_page_3 is not None

    assert len(tasks_page_3) == 5  # Last page should also contain 5 tasks


def test_delete_tasks_by_user_id():
    table = TaskTable()

    # Step 1: Insert 5 tasks for user123
    for i in range(5):
        table.insert_new_task(
            user_id="user1234",
            form_data=TaskForm(
                type=f"task_type_{i}",
                status=TaskStatus.QUEUED.value,
                extras={"key": f"value_{i}"},
            ),
        )

    # Step 2: Delete all tasks for user123
    deleted_tasks = table.delete_tasks_by_user_id("user1234")

    # Step 3: Assertions
    assert deleted_tasks is not None
    assert len(deleted_tasks) == 5  # All tasks should be deleted

    # Step 4: Verify that tasks are actually deleted (should return None when trying to get them)
    tasks_after_deletion = table.get_tasks_by_user_id(user_id="user1234", page=1, page_size=10)
    assert tasks_after_deletion is None or len(tasks_after_deletion) == 0  # No tasks left for this user

    no_deleted_tasks = table.delete_tasks_by_user_id("user1234")
    assert no_deleted_tasks is None
