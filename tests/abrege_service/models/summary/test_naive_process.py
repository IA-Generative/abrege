import os
import pytest


@pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY", None) or not os.environ.get("OPENAI_API_URL", None) or not os.environ.get("OPENAI_MODEL_NAME", None),
    reason="API key and url not set",
)
def test_prompt_summary_process():
    """
    Test the naive process of loading a dataset in streaming mode.
    """
    from datasets import load_dataset
    from evaluate import load
    from abrege_service.models.summary.naive import summarize_text
    from abrege_service.prompts.prompting import generate_prompt
    import openai

    # Chargement en streaming du sous-ensemble français
    dataset_stream = load_dataset(
        "csebuetnlp/xlsum",
        "french",
        cache_dir="tests/data/text",
        streaming=True,
    )

    rouge_metric = load("rouge")

    # Load the first batch of data
    client = openai.OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),
        base_url=os.environ.get("OPENAI_API_URL"),
    )
    dataset = dataset_stream["train"].shuffle(seed=42).take(10)

    predictions = []
    gt_summaries = []
    for data in dataset:
        assert "text" in data
        assert "summary" in data
        pred = summarize_text(
            model=os.environ.get("OPENAI_MODEL_NAME"),
            client=client,
            prompt=generate_prompt(
                "segement_summary_promt.jinja2",
                {"size": 100, "language": "français", "text": data["text"]},
            ),
        )
        predictions.append(pred)
        gt_summaries.append(data["summary"])

    # Calculate the Rouge score
    rouge_score = rouge_metric.compute(
        predictions=predictions,
        references=gt_summaries,
        use_stemmer=True,
    )
    print(f"Rouge score: {rouge_score}")
