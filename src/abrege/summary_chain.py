from typing import Literal

from langchain.chains import MapReduceDocumentsChain, ReduceDocumentsChain
from langchain.chains.llm import LLMChain
from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from langchain.chains.summarize import load_summarize_chain
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents.base import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import (
    PromptTemplate,
)
from langchain_core.runnables import (
    RunnableLambda,
    RunnablePassthrough,
)
from operator import itemgetter

from abrege.extractive_summary import (
    EmbeddingModel,
    build_text_prompt_text_rank,
    build_text_prompt_kmeans,
)
from abrege.prompt.template import prompt_template


MethodType = Literal[
    "text_rank", "map_reduce", "refine", "k-means", "stuff"
]


def summarize_chain_builder(
    llm,
    embedding_model: EmbeddingModel = None,
    context_size: int = 10_000,
    language: str = "english",
    method: MethodType = "text_rank",
    size: int = 200,
    summarize_template: str | None = None,
    map_template: str | None = None,
    reduce_template: str | None = None,
    question_template: str | None = None,
    refine_template: str | None = None,
    **kwargs,
):
    """Build a custom summarizing chain with your models, using the selected method for
    summarization

    Parameters
    -----------
    llm: Any
        chat model that will be tasked to execute the abstractive summary
    embedding_model: Model = None
        model chosen for embeddings, please use an instance of EmbeddingModel it with
        the custom class Model. Necessary with text_rank and k-means method
    context_size : int = 10_000
        context window size (in terms of len(text), not tokens) for which the llm can
        best exploit the context
    language : str = "french"
        language to use to write the summary
    method : Literal['text_rank', 'map_reduce', 'refine', 'kmeans', 'stuff']
        method to build the summary
        default to 'text_rank'
    summarize_template: str | None
        basic template for text_rank, k-means and small text
    map_template: str | None
        map template for map_reduce method
    reduce_template: str | None
        reduce template for map_reduce method
    question_template: str | None
        question template for refine method
    refine_template: str | None
        refine template for refine method

    Returns
    ----------
    Runnable[Any, str]
        custom chain that can be invoked to summarize text
    """
    new_chain = new_summarize_chain()
    info = {
        "llm": llm,
        "embedding_model": embedding_model,
        "context_size": context_size,
        "language": language,
        "method": method,
        "size": size,
        "summarize_template": summarize_template,
        "map_template": map_template,
        "reduce_template": reduce_template,
        "question_template": question_template,
        "refine_template": refine_template,
    }

    return RunnableLambda(lambda x: info | x) | new_chain


output_parser = StrOutputParser()


def text_rank_lambda(info):
    if info.get("embedding_model") is None:
        raise ValueError("embedding_model parameter necessecary for text_rank method")

    prompt = PromptTemplate.from_template(info["summarize_template"])

    extractive_summary = build_text_prompt_text_rank(
        info["text"], info["context_size"], info["embedding_model"]
    )

    return (
        RunnablePassthrough.assign(text=lambda _: extractive_summary)
        | prompt
        | info["llm"]
        | output_parser
    )


def kmeans_lambda(info):
    if info.get("embedding_model") is None:
        raise ValueError("embedding_model parameter necessecary for text_rank method")

    prompt = PromptTemplate.from_template(info["summarize_template"])

    extractive_summary = build_text_prompt_kmeans(
        info["text"], info["context_size"], info["embedding_model"]
    )

    return (
        RunnablePassthrough.assign(text=lambda _: extractive_summary)
        | prompt
        | info["llm"]
        | output_parser
    )


text_rank_chain = RunnableLambda(text_rank_lambda)
kmeans_chain = RunnableLambda(kmeans_lambda)


def split_lambda(info):
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=info["context_size"], chunk_overlap=0
    )

    split_texts = text_splitter.split_text(info["text"])
    split_docs = [Document(page_content=text) for text in split_texts]
    return RunnablePassthrough.assign(input_documents=lambda _: split_docs)


split_chain = RunnableLambda(split_lambda)


def refine_lambda(info):
    refine_chain = load_summarize_chain(
        llm=info["llm"],
        chain_type="refine",
        question_prompt=PromptTemplate.from_template(info["question_template"]),
        refine_prompt=PromptTemplate.from_template(info["refine_template"]),
        input_key="input_documents",
        output_key="summary_english",
    )

    return split_chain | refine_chain | RunnableLambda(itemgetter("summary_english"))


def map_reduce_lambda(info):
    map_prompt = PromptTemplate.from_template(info["map_template"])
    reduce_prompt = PromptTemplate.from_template(info["reduce_template"])
    map_chain = LLMChain(llm=info["llm"], prompt=map_prompt)
    reduce_chain = LLMChain(llm=info["llm"], prompt=reduce_prompt)
    combine_document_chain = StuffDocumentsChain(
        llm_chain=reduce_chain, document_variable_name="docs"
    )

    reduce_documents_chain = ReduceDocumentsChain(
        combine_documents_chain=combine_document_chain,
        collapse_documents_chain=combine_document_chain,
        token_max=info["context_size"],
    )

    final_chain = MapReduceDocumentsChain(
        llm_chain=map_chain,
        reduce_documents_chain=reduce_documents_chain,
        document_variable_name="docs",
        return_intermediate_steps=False,
        output_key="summary_english",
    )

    return split_chain | final_chain | RunnableLambda(itemgetter("summary_english"))


def stuff_lambda(info):
    prompt = PromptTemplate.from_template(info["summarize_template"])
    llm_chain = LLMChain(llm=info["llm"], prompt=prompt)

    return (split_chain
            | StuffDocumentsChain(
                llm_chain=llm_chain,
                document_variable_name="text",
                output_key="summary_english"
            )
            | RunnableLambda(itemgetter("summary_english"))
            )


refine_chain = RunnableLambda(refine_lambda)
map_reduce_chain = RunnableLambda(map_reduce_lambda)
stuff_chain = RunnableLambda(stuff_lambda)


method_to_chain = {
    "text_rank": text_rank_chain,
    "k-means": kmeans_chain,
    "refine": refine_chain,
    "map_reduce": map_reduce_chain,
    "stuff": stuff_chain,
}


def route(info):
    if info.get("method") not in method_to_chain:
        raise ValueError
    return method_to_chain[info["method"]]


def complete_input(info):
    if not info.get("context_size"):
        info["context_size"] = 2500
    if not info.get("language"):
        info["language"] = "french"
    if not info.get("size"):
        info["size"] = 200
    if not info.get("summarize_template"):
        info["summarize_template"] = prompt_template["summarize"]
    if not info.get("map_template"):
        info["map_template"] = prompt_template["map"]
    if not info.get("reduce_template"):
        info["reduce_template"] = prompt_template["reduce"]
    if not info.get("question_template"):
        info["question_template"] = prompt_template["question"]
    if not info.get("refine_template"):
        info["refine_template"] = prompt_template["refine"]

    return info


input_chain = RunnableLambda(complete_input)
route_chain = RunnableLambda(route)


def new_summarize_chain():
    return (
        input_chain
        | RunnableLambda(route)
    )
