import os
import pytest
from abrege_service.modules.audio import AudioVoskTranscriptionService
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
                file_path="tests/data/audio/1.wav",
                raw_filename="1.wav",
                content_type="audio/wav",
                ext=".wav",
                size=2,
            ),
        ),
    )

    return task


@pytest.mark.skipif(
    os.path.exists("abrege_service/data/models/vosk-model-small-fr-0.22") is False,
    reason="Model not found",
)
def test_audio_service(dummy_task: TaskModel):
    # wget https://alphacephei.com/vosk/models/vosk-model-small-fr-0.22.zip
    # unzip vosk-model-small-fr-0.22.zip -d abrege_service/data/models
    audio_service = AudioVoskTranscriptionService()
    task = audio_service.process_task(task=dummy_task)
    assert task.output.percentage == 1
