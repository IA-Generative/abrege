import pytest
from src.schemas.task import TaskModel, task_table, TaskForm, TaskStatus
from src.schemas.content import DocumentModel
from src.schemas.result import ResultModel, SummaryModel
from abrege_service.models.base import BaseSummaryService, TextResultNotGiven


@pytest.fixture(scope="module")
def dummy_task() -> TaskModel:
    task = task_table.insert_new_task(
        user_id="1",
        form_data=TaskForm(
            type="summary",
            status=TaskStatus.CREATED.value,
            updated_at=0,
            percentage=0.0,
            input=DocumentModel(
                created_at=0,
                file_path="tests/data/audio/1.wav",
                raw_filename="1.wav",
                content_type="audio/wav",
                ext=".wav",
                size=2,
            ),
            output=ResultModel(
                type="ocr",
                created_at=0,
                model_name="mock",
                model_version="mock",
                updated_at=0,
                texts_found=["Gauss"],
                percentage=0.5,
            ),
        ),
    )

    return task


@pytest.fixture(scope="module")
def mock_model_service() -> BaseSummaryService:
    class MockService(BaseSummaryService):
        def summarize(self, task: TaskModel, *args, **kwargs) -> TaskModel:
            result = SummaryModel(
                created_at=0,
                model_name="mock",
                model_version="mock",
                updated_at=0,
                texts_found=task.output.texts_found,
                percentage=1,
                summary="Done",
                word_count=1,
            )
            task = self.update_result_task(task=task, result=result, status=TaskStatus.COMPLETED.value, percentage=0.5)

            return task

    return MockService()


def test_base_model_service(dummy_task: TaskModel, mock_model_service: BaseSummaryService):
    task = mock_model_service.summarize(task=dummy_task)
    expected = SummaryModel(
        created_at=0,
        model_name="mock",
        model_version="mock",
        updated_at=0,
        texts_found=task.output.texts_found,
        percentage=1,
        summary="Done",
        word_count=1,
    )
    assert isinstance(task.output, SummaryModel)
    assert task.output == expected


def test_base_service_model_no_result(dummy_task: TaskModel, mock_model_service: BaseSummaryService):
    dummy_task.output.texts_found = []
    with pytest.raises(TextResultNotGiven):
        mock_model_service.process_task(task=dummy_task)

    dummy_task.output = None
    with pytest.raises(TextResultNotGiven):
        mock_model_service.process_task(task=dummy_task)
