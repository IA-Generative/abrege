import pytest
import openai
import os
from abrege_service.models.summary.map_reduce import (
    ChatOpenAI,
)
from src.schemas.task import TaskModel, TaskForm, task_table, TaskStatus
from src.schemas.result import ResultModel
from src.schemas.parameters import SummaryParameters
from datasets import load_dataset


@pytest.fixture(scope="module")
def mock_llm() -> ChatOpenAI:
    client = openai.OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),
        base_url=os.environ.get("OPENAI_API_BASE"),
    )
    model_name = [model.id for model in client.models.list()][0]
    return ChatOpenAI(
        model=model_name,
        temperature=0.0,
        api_key=os.environ.get("OPENAI_API_KEY"),
        base_url=os.environ.get("OPENAI_API_BASE"),
    )


@pytest.fixture(scope="module")
def dummy_task_large() -> TaskModel:
    dataset_stream = load_dataset(
        "csebuetnlp/xlsum",
        "french",
        cache_dir="tests/data/text",
        streaming=True,
    )
    dataset = dataset_stream["train"].shuffle(seed=42).take(20)
    text_found = []
    for data in dataset:
        assert "text" in data
        assert "summary" in data
        text_found.append(data["text"])

    task = task_table.insert_new_task(
        user_id="1",
        form_data=TaskForm(
            type="summary",
            status=TaskStatus.CREATED.value,
            updated_at=0,
            parameters=SummaryParameters(),
            output=ResultModel(
                type="ocr",
                created_at=0,
                model_name="mock",
                model_version="mock",
                updated_at=0,
                texts_found=text_found,
                percentage=0.5,
            ),
        ),
    )

    return task


def test_summary(mock_llm: ChatOpenAI, dummy_task_large: TaskModel):
    # service = LangChainMapReduceService(llm=mock_llm)
    # service.process_task(dummy_task_large)
    ...
