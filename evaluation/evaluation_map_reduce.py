import time
import asyncio
from abrege_service.models.summary.map_reduce import do_map_reduce
from abrege_service.schemas.params import ParamsSummarize
from tqdm import tqdm
from evaluation.client import dataset, rouge_metric, model_name
from src import __version__, __name__ as package_name
from bert_score import score


predictions = []
gt_summaries = []


def evaluate_summarization(dataset, model_name: str = model_name):
    """
    Evaluate the summarization model using Rouge and BertScore metrics.
    """
    params = ParamsSummarize()
    nb_calls = 0
    time_start = time.time()
    for data in tqdm(dataset):
        assert "text" in data
        assert "summary" in data
        pred = asyncio.run(
            do_map_reduce(
                list_str=[data["text"]],
                model=model_name,
                params=params,
                recursion_limit=20,
                num_tokens_limit=1226 * 300,
                ratio_word_token=0.75,
                temperature=0.0,
            )
        )
        predictions.append(pred["summary"])
        nb_calls += pred["nb_call"]
        gt_summaries.append(data["summary"])
    time_end = time.time()
    print(79 * "-")
    print(f"Package Version : {package_name} {__version__} prompt: {params.__class__.__name__}")
    print(f"\t Model: {model_name}")
    print(f"\t Number of predictions: {len(predictions)}")
    print(f"\t Time taken for summarization: {time_end - time_start} seconds")
    print(f"\t Average time per prediction: {(time_end - time_start) / len(predictions)} seconds")
    print(f"\t Number of API calls: {nb_calls}")
    print(f"\t Average time per API call: {(time_end - time_start) / nb_calls} seconds")
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
