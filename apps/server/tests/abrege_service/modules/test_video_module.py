import os
import pytest
from abrege_service.modules.video import VideoTranscriptionService
from src.schemas.task import TaskModel, task_table, TaskForm, TaskStatus
from src.schemas.content import DocumentModel


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
                file_path="tests/data/video/bonjour.mp4",
                raw_filename="bonjour.mp4",
                content_type="video/mp4",
                ext=".mp4",
                size=2,
            ),
        ),
    )

    return task


@pytest.mark.skipif(
    os.path.exists("/app/data/models/vosk-model-small-fr-0.22") is False,
    reason="Model not found",
)
def test_video_service(dummy_task: TaskModel):
    video_service = VideoTranscriptionService()
    content = dummy_task.input
    task = video_service.process_task(task=dummy_task)
    assert task.output.percentage == 1
    # Check no change into content
    assert task.input == content
