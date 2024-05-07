import os
from typing import Literal

from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from langchain.chains import MapReduceDocumentsChain, ReduceDocumentsChain
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
from langchain_openai import ChatOpenAI

from abrege.extractive_summary import (
    EmbeddingModel,
    build_text_prompt,
    build_text_prompt_kmeans,
)

summarize_template = """
Write a summary of the following text:
{text}
SUMMARY :
"""

map_template = """The following is a set of documents
{docs}
Based on this list of docs, please identify the main themes
Helpful Answer:"""
map_prompt = PromptTemplate.from_template(map_template)

reduce_template = """The following is set of summaries
{docs}
Take these and distill it into a final, consolidated summary written of the main themes.
Helpful Answer:"""
reduce_prompt = PromptTemplate.from_template(reduce_template)

question_prompt_template = """Write a concise summary of the following :
{text}
CONCISE SUMMARY:"""
question_prompt = PromptTemplate.from_template(question_prompt_template)
refine_template = (
    "Your job is to produce a final summary\n"
    "We have provided an existing summary up to a certain point: {existing_answer}\n"
    "We have the opportunity to refine the existing summary"
    "(only if needed) with some more context below.\n"
    "------------\n"
    "{text}\n"
    "------------\n"
    "Given the new context, refine the original summary in Italian"
    "If the context isn't useful, return the original summary."
)
refine_prompt = PromptTemplate.from_template(refine_template)

template = (
    "You are a helpful assistant that translates {input_language} to {output_language}."
)
system_message_prompt = SystemMessagePromptTemplate.from_template(template)
human_template = (
    "Translate this sentence from {input_language} to {output_language}. {text}"
)
human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)


MethodType = Literal["text_rank", "map_reduce", "refine", "k-means", "stuff"]


def summarize_chain_builder(
    llm=None,
    llm_context_window_size: int = 2000,
    embedding_model: EmbeddingModel = None,
    language: str = "english",
    method: MethodType = "text_rank",
    summary_template: str | None = None,
    **kwargs,
):
    """Build a custom summarizing chain with your models, using the selected method for
    summarization

    Parameters
    -----------
    llm: Any = None
        chat model that will be tasked to execute the abstractive summary
        default to miom api if None
    llm_context_window_size : int = 5000
        context window size (in terms of len(text), not tokens) for which the llm can
        best exploit the context
    embedding_model: Model = None
        model chosen for embeddings, please use an instance of EmbeddingModel it with
        the custom class Model
        default to miom api if None
    language : str = "french"
        language to use to write the summary
    method : Literal['text_rank', 'map_reduce', 'refine', 'kmeans', 'stuff']
        method to build the summary
        default to 'text_rank'
    summary_prompt : str
        text template to create a summary prompt
        default to basic template

    Returns
    ----------
    Runnable[Any, str]
        custom chain that can be invoked to summarize text
    """

    if llm is None:
        OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
        OPENAI_API_BASE = os.environ["OPENAI_API_BASE"]
        llm = ChatOpenAI(api_key=OPENAI_API_KEY, openai_api_base=OPENAI_API_BASE)

    if embedding_model is None:
        OPENAI_EMBEDDING_API_KEY = os.environ["OPENAI_EMBEDDING_API_KEY"]
        OPENAI_EMBEDDING_API_BASE = os.environ["OPENAI_EMBEDDING_API_BASE"]

        openai_ef = OpenAIEmbeddingFunction(
            api_key=OPENAI_EMBEDDING_API_KEY, api_base=OPENAI_EMBEDDING_API_BASE
        )
        embedding_model = EmbeddingModel(openai_ef)  # mal
        assert embedding_model.model_class == "OpenAIEmbeddingFunction"

    if summary_template is None:
        summary_template = summarize_template

    match method:
        case "text_rank":

            @chain
            def custom_chain(text):
                extractive_summary = build_text_prompt(
                    text, llm_context_window_size, embedding_model, **kwargs
                )
                summarize_prompt = PromptTemplate.from_template(summary_template)
                prompt1 = summarize_prompt.invoke({"text": extractive_summary})
                output1 = llm.invoke(prompt1)
                output_parser = StrOutputParser()
                return output_parser.invoke(output1)

        case "refine":

            @chain
            def custom_chain(text):
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
                    chunk_size=4000, chunk_overlap=0
                )
                split_texts = text_splitter.split_text(text)
                split_docs = [Document(page_content=text) for text in split_texts]
                result = refine_chain.invoke(
                    {"input_documents": split_docs}, return_only_outputs=True
                )
                return result["output_text"]

        case "map_reduce":

            @chain
            def custom_chain(text):
                map_chain = map_prompt | llm
                reduce_chain = reduce_prompt | llm
                combine_document_chain = StuffDocumentsChain(
                    llm_chain=reduce_chain, document_variable_name="docs"
                )

                reduce_documents_chain = ReduceDocumentsChain(
                    combine_documents_chain=combine_document_chain,
                    collapse_documents_chain=combine_document_chain,
                    token_max=4000,
                )

                map_reduce_chain = MapReduceDocumentsChain(
                    llm_chain=map_chain,
                    reduce_documents_chain=reduce_documents_chain,
                    document_variable_name="docs",
                    return_intermediate_steps=False,
                )
                text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
                    chunk_size=4000, chunk_overlap=0
                )
                split_text = text_splitter.split_text(text)
                split_docs = [Document(page_content=text) for text in split_text]
                result = map_reduce_chain.invoke(split_docs)
                return result["output_text"]

        case "k-means":

            @chain
            def custom_chain(text: str):
                extractive_summary = build_text_prompt_kmeans(
                    text, llm_context_window_size, embedding_model, **kwargs
                )
                summarize_prompt = PromptTemplate.from_template(summary_template)
                prompt1 = summarize_prompt.invoke({"text": extractive_summary})
                output = llm.invoke(prompt1)
                output_parser = StrOutputParser()
                return output_parser.invoke(output)

        case "stuff":

            @chain
            def custom_chain(text: str):
                summarize_prompt = PromptTemplate.from_template(summary_template)
                llm_chain = summarize_prompt | llm
                stuff_chain = StuffDocumentsChain(
                    llm_chain=llm_chain, document_variable_name="text"
                )
                doc = Document(page_content=text)
                return stuff_chain.invoke([doc])["output_text"]

        case _:
            raise ValueError(
                f"""method should be one of 'text_rank', 'refine', 'k-means' or
                'map_reduce', got {method}"""
            )

    # Handle with a simple call to llm small text
    @chain
    def small_text_chain(text: str):
        if llm.get_num_tokens(text) < 3000:
            summarize_prompt = PromptTemplate.from_template(summary_template)
            simple_chain = summarize_prompt | llm
            return simple_chain.invoke(text)
        else:
            return custom_chain.invoke(text)

    @chain
    def translate_chain(text: str):
        summary_english = small_text_chain.invoke(text)
        if language != "English":
            chat_prompt = ChatPromptTemplate.from_messages(
                [system_message_prompt, human_message_prompt]
            )
            summary = llm.invoke(
                chat_prompt.format_prompt(
                    input_language="English",
                    output_language="French",
                    text=summary_english,
                ).to_messages()
            )
            return summary.content
        else:
            return summary_english

    return translate_chain
