import os
import pytest
from src.schemas.task import TaskModel, TaskStatus, task_table, TaskForm
from src.schemas.content import DocumentModel
from abrege_service.modules.image import ImageFromVLM
from openai import AsyncOpenAI

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL")
VLM_MODEL_NAME = os.environ.get("VLM_MODEL_NAME")
is_openai_set = all([OPENAI_API_KEY, OPENAI_BASE_URL, VLM_MODEL_NAME])


@pytest.fixture(scope="module")
def dummy_task_pdf() -> TaskModel:
    task = task_table.insert_new_task(
        user_id="1",
        form_data=TaskForm(
            type="summary",
            status=TaskStatus.CREATED.value,
            updated_at=0,
            input=DocumentModel(
                created_at=0,
                file_path="tests/test_data/elysee-module-24161-fr.pdf",
                raw_filename="elysee-module-24161-fr.pdf",
                content_type="application/pdf",
                ext=".pdf",
                size=2,
            ),
        ),
    )

    return task


@pytest.fixture(scope="module")
def dummy_task_image() -> TaskModel:
    task = task_table.insert_new_task(
        user_id="1",
        form_data=TaskForm(
            type="summary",
            status=TaskStatus.CREATED.value,
            updated_at=0,
            input=DocumentModel(
                created_at=0,
                file_path="tests/test_data/minister-logo.png",
                raw_filename="minister-logo.png",
                content_type="image/png",
                ext=".png",
                size=2,
            ),
        ),
    )

    return task


@pytest.mark.skipif(condition=not is_openai_set, reason="Openai model not set")
def test_pdf_from_vlm(dummy_task_pdf: TaskModel):
    client = AsyncOpenAI(
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_BASE_URL,
    )
    obj = ImageFromVLM(
        client=client,
        model_name=VLM_MODEL_NAME,
    )
    task = obj.task_to_text(dummy_task_pdf)
    assert task.output.percentage == 1
    assert len(task.output.texts_found) == 3


@pytest.mark.skipif(condition=not is_openai_set, reason="Openai model not set")
def test_image_from_vlm(dummy_task_image: TaskModel):
    client = AsyncOpenAI(
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_BASE_URL,
    )
    obj = ImageFromVLM(
        client=client,
        model_name=VLM_MODEL_NAME,
    )
    task = obj.task_to_text(dummy_task_image)
    assert task.output.percentage == 1
    assert len(task.output.texts_found) == 1


@pytest.mark.skipif(condition=not is_openai_set, reason="Openai model not set")
def test_file_not_implem_from_vlm(dummy_task_image: TaskModel):
    dummy_task_image.input.content_type = "dsdsd"
    client = AsyncOpenAI(
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_BASE_URL,
    )
    obj = ImageFromVLM(
        client=client,
        model_name=VLM_MODEL_NAME,
    )
    with pytest.raises(NotImplementedError):
        obj.task_to_text(dummy_task_image)
