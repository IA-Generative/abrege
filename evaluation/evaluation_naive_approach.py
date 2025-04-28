import time
from abrege_service.models.summary.naive import summarize_text
from abrege_service.prompts.prompting import generate_prompt
from tqdm import tqdm
from evaluation.client import client, dataset, rouge_metric, model_name
from src import __version__, __name__ as package_name
from bert_score import score


predictions = []
gt_summaries = []


def evaluate_summarization(dataset, client=client, model_name: str = model_name):
    """
    Evaluate the summarization model using Rouge and BertScore metrics.
    """
    prompt_template = "segement_summary_promt.jinja2"
    time_start = time.time()
    for data in tqdm(dataset):
        assert "text" in data
        assert "summary" in data
        pred = summarize_text(
            model="gemma3",
            client=client,
            prompt=generate_prompt(
                prompt_template,
                {"size": None, "language": "français", "text": data["text"]},
            ),
        )
        predictions.append(pred)
        gt_summaries.append(data["summary"])
    time_end = time.time()
    print(79 * "-")
    print(f"Package Version : {package_name} {__version__} prompt: {prompt_template}")
    print(f"\t Model: {model_name}")
    print(f"\t Number of predictions: {len(predictions)}")
    print(f"\t Time taken for summarization: {time_end - time_start} seconds")
    print(f"\t Average time per prediction: {(time_end - time_start) / len(predictions)} seconds")
    # Calculate the Rouge score
    rouge_score = rouge_metric.compute(
        predictions=predictions,
        references=gt_summaries,
        use_stemmer=True,
    )
    print(f"\t -> Rouge score: {rouge_score}")
    P, R, F1 = score(predictions, gt_summaries, lang="others", verbose=False)
    print(f"\t -> Precision: {P.mean()}, Recall: {R.mean()}, F1: {F1.mean()}")
    print(79 * "-")
    return rouge_score, P.mean(), R.mean(), F1.mean()


if __name__ == "__main__":
    rouge_score, P, R, F1 = evaluate_summarization(dataset)
