import pytest
import os, sys, random
import logging

import statistics
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain.docstore.document import Document

from tqdm import tqdm
import nltk

sys.path.append(str(Path(__file__).parent.parent / "src"))
from selfcheck import SelfCheckGPT, selfcheck

# poetry add datasets
from datasets import load_dataset

dataset = load_dataset("ZhongshengWang/Alpaca-cnn-dailymail")
dataset = {
    "train": {
        "input": [
            p.read_text() for p in Path("/home/alex/CODE/abrege/texts").glob("*.txt")
        ]
    }
}
OPENAI_API_BASE = os.environ["OPENAI_API_BASE"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

llm = ChatOpenAI(
    api_key=OPENAI_API_KEY,
    openai_api_base=OPENAI_API_BASE,
    temperature=0,
    model="mixtral",
)

from summary_chain import summarize_chain_builder, EmbeddingModel

embeddings = HuggingFaceEmbeddings(
    model_name=os.environ["EMBEDDING_MODEL_PATH"]
)  # plus de 13 min

if type(embeddings).__name__ == "HuggingFaceEmbeddings":
    model_class = "HuggingFaceEmbeddings"
else:
    model_class = "hugging_hub"

embedding_model = EmbeddingModel(embeddings, model_class)


class TestClass:

    dataset = dataset

    @staticmethod
    def eval_chain(
        custom_chain, iter_of_str, progress_bar: bool = True, reversed: int = 5
    ) -> list[float]:
        metrics = []
        iter_ = tqdm(iter_of_str) if progress_bar else iter_of_str
        sumup_array = [custom_chain.invoke(text_to_sumup) for text_to_sumup in iter_]
        for i, (text_to_sumup, sumup) in enumerate(zip(iter_of_str, sumup_array)):
            metric = selfcheck(
                llm=llm,
                docs=[Document(page_content=text_to_sumup)],
                summarize_to_eval=sumup,
            )
            metrics.append(metric)
        reversed_metrics = []
        for text_to_sumup, sumup in zip(iter_of_str, sumup_array):
            sentences = nltk.tokenize.sent_tokenize(text_to_sumup)
            chosen_sentences = random.sample(sentences, reversed)
            reversed_metric = selfcheck(
                llm=llm,
                docs=[Document(page_content=sumup)],
                summarize_to_eval="".join(chosen_sentences),
            )
            reversed_metrics.append(reversed_metric)
        return metrics, reversed_metrics

    @staticmethod
    def get_metrics_from_method(method: str, n: int = 5):
        text_rank_chain = summarize_chain_builder(
            method=method, embedding_model=embedding_model, llm=llm
        )

        metrics, rmetrics = TestClass.eval_chain(
            text_rank_chain, TestClass.dataset["train"]["input"][:n]
        )
        print(f"For {method=}, {metrics=}, {rmetrics=}")
        return metrics, rmetrics

    def test_textrank(self, n: int = 5):
        metrics, rmetrics = TestClass.get_metrics_from_method("text_rank", n=n)
        assert statistics.mean(metrics) >= 0.7

    def test_kmeans(self, n: int = 5):
        metrics, rmetrics = TestClass.get_metrics_from_method("text_rank", n=n)
        assert statistics.mean(metrics) >= 0.7


if __name__ == "__main__":
    to_print = ""
    for method in {"text_rank", "refine", "map_reduce"}:
        metrics, rmetrics = TestClass.get_metrics_from_method(method)
        msg = f"{method=} {statistics.mean(metrics)=} {metrics}\n"
        print(msg)
        to_print += msg

    print(to_print)
