import asyncio
import time

from bert_score import score
from langchain.docstore.document import Document
from langchain_huggingface import HuggingFaceEmbeddings
from tqdm import tqdm
from statistics import fmean
from evaluation.client import dataset, llm_judge, model_name, rouge_metric
from evaluation.selfcheck import selfcheck
from src import __name__ as package_name
from src import __version__
from src.schemas.parameters import SummaryParameters

from evaluation.mapreduce import do_map_reduce

predictions = []
gt_summaries = []


def evaluate_summarization(dataset, model_name: str = model_name):
    """
    Evaluate the summarization model using Rouge and BertScore metrics.
    """
    params = SummaryParameters()
    nb_calls = 0
    time_start = time.time()
    for data in tqdm(dataset):
        assert "text" in data
        assert "summary" in data
        pred = asyncio.run(
            do_map_reduce(
                list_str=[data["text"]],
                params=params,
                recursion_limit=20,
                num_tokens_limit=1226 * 300,
            )
        )
        predictions.append(pred.summary)
        nb_calls += pred.nb_call
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

    chroma_embedding = HuggingFaceEmbeddings(model_name="OrdalieTech/Solon-embeddings-base-0.1")  # le téléchargement prend plus de 13 min
    selfcheck_scores = []
    for i, item in enumerate(dataset):
        chroma_embedding = HuggingFaceEmbeddings(model_name="OrdalieTech/Solon-embeddings-base-0.1")
        metric = selfcheck(
            llm=llm_judge,
            chroma_embedding=chroma_embedding,
            embedding_model=None,
            docs=[Document(page_content=item["text"])],
            summarize_to_eval=predictions[i],
            mode="full",
            k_max=10
        )
        selfcheck_scores.append(metric)
    print(selfcheck_scores)
    print(f"\t Light SelfCheck score : mean={fmean(selfcheck_scores):.2%}")

    print(79 * "-")
    
    return rouge_score, P.mean(), R.mean(), F1.mean()


if __name__ == "__main__":
    # uv run --env-file .env python -m evaluation.evaluation_map_reduce
    rouge_score, P, R, F1 = evaluate_summarization(dataset)
    
