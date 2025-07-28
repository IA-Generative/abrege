import pytest
from abrege_service.modules.base import BaseService, NoGivenInput
from src.schemas.task import TaskModel, TaskStatus, task_table, TaskForm
from src.schemas.content import DocumentModel
from src.schemas.result import ResultModel


@pytest.fixture(scope="module")
def mock_base_service() -> BaseService:
    class MockeBase(BaseService):
        def __init__(self, content_type_allowed=...):
            super().__init__(content_type_allowed)

        def task_to_text(self, task: TaskModel, **kwargs):
            if task.output is None:
                task.output = ResultModel(
                    type="process",
                    created_at=0,
                    model_name="mock",
                    model_version="1",
                    updated_at=0,
                    percentage=0,
                )
            task.output.percentage = 0.5
            task = self.update_task(task=task, result=task.output, status=TaskStatus.IN_PROGRESS.value)
            return task

    return MockeBase(content_type_allowed=["application/pdf"])


@pytest.fixture(scope="module")
def dummy_task() -> TaskModel:
    task = task_table.insert_new_task(
        user_id="1",
        form_data=TaskForm(
            type="summary",
            status=TaskStatus.CREATED.value,
            updated_at=0,
            input=DocumentModel(
                created_at=0,
                file_path="ft://mock.txt",
                raw_filename="mock.txt",
                content_type="application/pdf",
                ext=".pdf",
                size=2,
            ),
        ),
    )

    return task


def test_base_service_is_available(mock_base_service: BaseService):
    assert mock_base_service.is_availble(content_type="application/pdf")
    assert not mock_base_service.is_availble(content_type="image/jpeg")


def test_base_srevice_update_task(mock_base_service: BaseService, dummy_task: TaskModel):
    expected_result = ResultModel(
        type="ocr",
        created_at=0,
        model_name="mock",
        model_version="1",
        updated_at=0,
        percentage=0.2,
    )
    actual_task = mock_base_service.update_task(task=dummy_task, result=expected_result, status=TaskStatus.STARTED.value)

    assert actual_task.output == expected_result
    assert actual_task.status == TaskStatus.STARTED.value


def test_base_service_process_task(mock_base_service: BaseService, dummy_task: TaskModel):
    actual_task = mock_base_service.process_task(dummy_task)
    assert actual_task.output.percentage == 0.5
    assert actual_task.status == TaskStatus.IN_PROGRESS.value

    with pytest.raises(NotImplementedError):
        dummy_task.input.content_type = "image/jpeg"
        mock_base_service.process_task(dummy_task)

    with pytest.raises(NoGivenInput):
        dummy_task.input = None
        mock_base_service.process_task(dummy_task)
