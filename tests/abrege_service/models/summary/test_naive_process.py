import os
import pytest
import math
from abrege_service.models.summary.naive import (
    summarize_text,
    merge_summaries,
)
from abrege_service.prompts.prompting import generate_prompt
from src.schemas.task import task_table, TaskStatus, TaskForm
import openai
from datasets import load_dataset

is_openai_available = (
    not os.environ.get("OPENAI_API_KEY", None) or not os.environ.get("OPENAI_API_BASE", None) or not os.environ.get("OPENAI_API_MODEL", None)
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
    dataset = dataset_stream["train"].shuffle(seed=42).take(2)

    predictions = []
    for data in dataset:
        assert "text" in data
        assert "summary" in data
        pred = summarize_text(
            model=os.environ.get("OPENAI_API_MODEL"),
            client=client,
            prompt=generate_prompt(
                "segement_summary_promt.jinja2",
                {"size": 100, "language": "français", "text": data["text"]},
            ),
        )
        assert isinstance(pred, str)
        predictions.append(pred)

    assert len(predictions) == 2


@pytest.mark.skipif(is_openai_available, reason=message)
def test_merge_summary_small_text():
    """
    Test the naive process of loading a dataset in streaming mode.
    """

    # Load the first batch of data
    client = openai.OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),
        base_url=os.environ.get("OPENAI_API_BASE"),
    )
    task = task_table.insert_new_task(
        user_id="test",
        form_data=TaskForm(type="summary", status=TaskStatus.CREATED.value),
    )

    task, nb_call = merge_summaries(
        task=task,
        summaries=["test", "test2"],
        model=os.environ.get("OPENAI_API_MODEL"),
        client=client,
    )
    assert task.status == TaskStatus.COMPLETED.value
    assert nb_call == 1
    task_table.delete_task_by_id(task.id)


@pytest.mark.skipif(True, reason=message)
def test_merge_summary_large_text():
    dataset_stream = load_dataset(
        "csebuetnlp/xlsum",
        "french",
        cache_dir="tests/data/text",
        streaming=True,
    )
    client = openai.OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),
        base_url=os.environ.get("OPENAI_API_BASE"),
    )

    task = task_table.insert_new_task(
        user_id="test",
        form_data=TaskForm(type="summary", status=TaskStatus.CREATED.value),
    )
    n = 3
    dataset = dataset_stream["train"].shuffle(seed=42).take(n)

    texts = []
    for data in dataset:
        texts.append(data["text"])

    # Here work with gemma3
    task, nb_call = merge_summaries(
        task=task,
        summaries=texts,
        model=os.environ.get("OPENAI_API_MODEL"),
        client=client,
    )
    assert task.status == TaskStatus.COMPLETED.value
    assert nb_call == int(math.log(n, 2) + 1)
    assert task.result.percentage == 1
    task_table.delete_task_by_id(task.id)
