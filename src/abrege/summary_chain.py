from typing import Literal
import concurrent.futures

from langchain.chains import MapReduceDocumentsChain, ReduceDocumentsChain
from langchain.chains.llm import LLMChain
from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from langchain.chains.summarize import load_summarize_chain
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents.base import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import (
    PromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    ChatPromptTemplate,
)
from langchain_core.runnables import chain

from abrege.extractive_summary import (
    EmbeddingModel,
    build_text_prompt_text_rank,
    build_text_prompt_kmeans,
)
from abrege.prompt.template import prompt_template, experimental_prompt_template

template = (
    "You are a helpful assistant that translates {input_language} to {output_language}."
)
system_message_prompt = SystemMessagePromptTemplate.from_template(template)
human_template = "Translate this sentence from {input_language} to {output_language}. Adds no comments (before or after) in addition to the translation. {text}"
human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

MethodType = Literal[
    "text_rank", "map_reduce", "refine", "k-means", "stuff", "text_rank2", "k-means2"
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

    if method == "text_rank":
        if embedding_model is None:
            raise ValueError("embedding_model parameter necessary for text_rank method")

        @chain
        def custom_chain(text):
            nonlocal summarize_template
            extractive_summary = build_text_prompt_text_rank(
                text, context_size, embedding_model, **kwargs
            )
            extractive_summary = "".join(extractive_summary)
            if summarize_template is None:
                summarize_template = prompt_template["summarize"]
            summarize_prompt = PromptTemplate.from_template(summarize_template)
            prompt1 = summarize_prompt.invoke(
                {"text": extractive_summary, "size": size}
            )
            output1 = llm.invoke(prompt1)
            output_parser = StrOutputParser()
            return output_parser.invoke(output1)

    elif method == "refine":

        @chain
        def custom_chain(text):
            nonlocal question_template
            nonlocal refine_template

            if question_template is None:
                question_template = prompt_template["question"]
            if refine_template is None:
                refine_template = prompt_template["refine"]
            question_prompt = PromptTemplate.from_template(question_template)
            refine_prompt = PromptTemplate.from_template(refine_template)
            refine_chain = load_summarize_chain(
                llm=llm,
                chain_type="refine",
                question_prompt=question_prompt,
                refine_prompt=refine_prompt,
                return_intermediate_steps=True,
                input_key="input_documents",
                output_key="output_text",
            )

            text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
                chunk_size=context_size, chunk_overlap=0
            )
            split_texts = text_splitter.split_text(text)
            split_docs = [Document(page_content=text) for text in split_texts]
            result = refine_chain.invoke(
                {"input_documents": split_docs, "size": size}, return_only_outputs=True
            )
            return result["output_text"]

    elif method == "map_reduce":

        @chain
        def custom_chain(text):
            nonlocal map_template
            nonlocal reduce_template

            if map_template is None:
                map_template = prompt_template["map"]
            if reduce_template is None:
                reduce_template = prompt_template["reduce"]
            map_prompt = PromptTemplate.from_template(map_template)
            reduce_prompt = PromptTemplate.from_template(reduce_template)
            map_chain = LLMChain(llm=llm, prompt=map_prompt)
            reduce_chain = LLMChain(llm=llm, prompt=reduce_prompt)
            combine_document_chain = StuffDocumentsChain(
                llm_chain=reduce_chain, document_variable_name="docs"
            )

            reduce_documents_chain = ReduceDocumentsChain(
                combine_documents_chain=combine_document_chain,
                collapse_documents_chain=combine_document_chain,
                token_max=10_000,  # What ?
            )

            map_reduce_chain = MapReduceDocumentsChain(
                llm_chain=map_chain,
                reduce_documents_chain=reduce_documents_chain,
                document_variable_name="docs",
                return_intermediate_steps=False,
            )
            text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
                chunk_size=context_size, chunk_overlap=0
            )
            split_text = text_splitter.split_text(text)
            split_docs = [Document(page_content=text) for text in split_text]
            result = map_reduce_chain.invoke(
                {"input_documents": split_docs, "size": size}
            )
            return result["output_text"]

    elif method == "k-means":

        @chain
        def custom_chain(text: str):
            nonlocal summarize_template
            if summarize_template is None:
                summarize_template = prompt_template["summarize"]
            summarize_prompt = PromptTemplate.from_template(summarize_template)

            extractive_summary = build_text_prompt_kmeans(
                text, context_size, embedding_model, **kwargs
            )
            extractive_summary = "".join(extractive_summary)
            prompt1 = summarize_prompt.invoke({"text": text, "size": size})
            output = llm.invoke(prompt1)
            output_parser = StrOutputParser()
            return output_parser.invoke(output)

    elif method == "stuff":

        @chain
        def custom_chain(text: str):
            nonlocal summarize_template
            if summarize_template is None:
                summarize_template = prompt_template["summarize"]
            summarize_prompt = PromptTemplate.from_template(summarize_template)

            llm_chain = LLMChain(llm=llm, prompt=summarize_prompt)
            stuff_chain = StuffDocumentsChain(
                llm_chain=llm_chain, document_variable_name="text"
            )
            doc = Document(page_content=text)
            return stuff_chain.invoke({"input_documents": [doc], "size": size})[
                "output_text"
            ]

    elif method == "text_rank2":

        @chain
        def custom_chain(text: str):

            map_prompt = experimental_prompt_template["map"]
            combine_prompt = experimental_prompt_template["combine"]
            list_chunk = build_text_prompt_text_rank(
                text, context_size, embedding_model, chunk_type="chunks"
            )
            map_chain = load_summarize_chain(
                llm=llm, chain_type="stuff", prompt=map_prompt
            )
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                list_doc = [[Document(page_content=chunk)] for chunk in list_chunk]
                future_summaries = executor.map(map_chain.invoke, list_doc)
                summary_list = [summary["output_text"] for summary in future_summaries]

            summaries = "\n".join(summary_list)
            summaries = Document(page_content=summaries)
            reduce_chain = load_summarize_chain(
                llm=llm, chain_type="stuff", prompt=combine_prompt
            )
            output = reduce_chain.invoke([summaries])
            return output["output_text"]

    elif method == "k-means2":

        @chain
        def custom_chain(text: str):
            map_prompt = experimental_prompt_template["map"]
            combine_prompt = experimental_prompt_template["combine"]
            list_chunk = build_text_prompt_kmeans(
                text, 5000, embedding_model, chunk_type="chunks"
            )
            map_chain = load_summarize_chain(
                llm=llm, chain_type="stuff", prompt=map_prompt
            )
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                list_doc = [[Document(page_content=chunk)] for chunk in list_chunk]
                future_summaries = executor.map(map_chain.invoke, list_doc)
                summary_list = [summary["output_text"] for summary in future_summaries]

            summaries = "\n".join(summary_list)
            summaries = Document(page_content=summaries)
            reduce_chain = load_summarize_chain(
                llm=llm, chain_type="stuff", prompt=combine_prompt
            )
            output = reduce_chain.invoke([summaries])
            return output["output_text"]

    else:
        raise ValueError(
            f"""method should be one of 'text_rank', 'refine', 'k-means' or
            'map_reduce', got {method}"""
        )

    # Handle with a simple call to llm small text
    @chain
    def small_text_chain(text: str):
        if llm.get_num_tokens(text) < 3000:
            nonlocal summarize_template
            if summarize_template is None:
                summarize_template = prompt_template["summarize"]
            summarize_prompt = PromptTemplate.from_template(summarize_template)
            simple_chain = summarize_prompt | llm
            simple_summary = simple_chain.invoke({"text": text, "size": size})
            return simple_summary.content
        else:
            return custom_chain.invoke(text)

    @chain
    def translate_chain(text: str):
        summary_english = small_text_chain.invoke(text)
        if language.lower() != "english":
            chat_prompt = ChatPromptTemplate.from_messages(
                [system_message_prompt, human_message_prompt]
            )
            summary = llm.invoke(
                chat_prompt.format_prompt(
                    input_language="English",
                    output_language=language,
                    text=summary_english,
                ).to_messages()
            )
            return summary.content
        else:
            return summary_english

    return translate_chain
