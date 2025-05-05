import os
import pytest
import math
import openai
import json
from datasets import load_dataset

from abrege_service.models.summary.naive import summarize_text, NaiveSummaryService
from abrege_service.prompts.prompting import generate_prompt

from src.schemas.task import task_table, TaskStatus, TaskForm, TaskModel
from src.schemas.result import ResultModel, SummaryModel


is_openai_available = (
    not os.environ.get("OPENAI_API_KEY", None) and not os.environ.get("OPENAI_API_BASE", None) and not os.environ.get("OPENAI_API_MODEL", None)
)

message = "API key and url not set"


@pytest.mark.skipif(is_openai_available, reason=message)
def test_prompt_summary_process():
    """
    Test the naive process of loading a dataset in streaming mode.
    """

    # Chargement en streaming du sous-ensemble français
    dataset_stream = load_dataset(
        "csebuetnlp/xlsum",
        "french",
        cache_dir="tests/data/text",
        streaming=True,
    )

    # Load the first batch of data
    client = openai.OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),
        base_url=os.environ.get("OPENAI_API_BASE"),
    )
    model_name = [model.id for model in client.models.list()][0]
    dataset = dataset_stream["train"].shuffle(seed=42).take(2)

    predictions = []
    for data in dataset:
        assert "text" in data
        assert "summary" in data
        pred = summarize_text(
            model=model_name,
            client=client,
            prompt=generate_prompt(
                "segement_summary_promt.jinja2",
                {"size": 100, "language": "français", "text": data["text"]},
            ),
        )
        assert isinstance(pred, str)
        predictions.append(pred)

    assert len(predictions) == 2


@pytest.fixture(scope="module")
def dummy_task() -> TaskModel:
    task = task_table.insert_new_task(
        user_id="1",
        form_data=TaskForm(
            type="summary",
            status=TaskStatus.CREATED.value,
            updated_at=0,
            result=ResultModel(
                type="ocr",
                created_at=0,
                model_name="mock",
                model_version="mock",
                updated_at=0,
                texts_found=["Je suis Nathan un plombier du code, j'essai de trouver des solutions pour les autres dans le domaine de la santé"],
                percentage=0.5,
            ),
        ),
    )

    return task


@pytest.mark.skipif(is_openai_available, reason=message)
def test_merge_summary_small_text(dummy_task: TaskModel):
    """
    Test the naive process of loading a dataset in streaming mode.
    """

    # Load the first batch of data
    client = openai.OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),
        base_url=os.environ.get("OPENAI_API_BASE"),
    )
    model_name = [model.id for model in client.models.list()][0]
    summary_service = NaiveSummaryService(model_name=model_name, client=client, size=500, language="francais")
    task = summary_service.process_task(task=dummy_task)
    assert isinstance(task.result, SummaryModel)
    assert task.status == TaskStatus.COMPLETED.value
    assert task.result.nb_llm_calls == 1
    assert task.result.percentage == 1
    assert "Nathan" in task.result.summary


@pytest.fixture(scope="module")
def dummy_task_large() -> TaskModel:
    dataset_stream = load_dataset(
        "csebuetnlp/xlsum",
        "french",
        cache_dir="tests/data/text",
        streaming=True,
    )
    dataset = dataset_stream["train"].shuffle(seed=42).take(3)
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
            result=ResultModel(
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


@pytest.mark.skipif(is_openai_available, reason=message)
def test_merge_summary_large_text(dummy_task_large: TaskModel):
    """
    Test the naive process of loading a dataset in streaming mode.
    """

    # Load the first batch of data
    client = openai.OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),
        base_url=os.environ.get("OPENAI_API_BASE"),
    )
    model_name = [model.id for model in client.models.list()][0]
    summary_service = NaiveSummaryService(model_name=model_name, client=client, size=500, language="francais")
    task = summary_service.process_task(task=dummy_task_large)
    assert isinstance(task.result, SummaryModel)
    assert task.status == TaskStatus.COMPLETED.value
    with open("tests/data/test_merge_summary_large_text.json", "w") as f:
        json.dump(task.result.model_dump(), f, indent=2)

    assert task.result.nb_llm_calls == int(math.log(len(dummy_task_large.result.texts_found), 2) + 1)
    assert task.result.percentage == 1
