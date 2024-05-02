import os
from typing import Literal

from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from dotenv import load_dotenv
from langchain.chains import MapReduceDocumentsChain, ReduceDocumentsChain
from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from langchain.chains.llm import LLMChain
from langchain.chains.summarize import load_summarize_chain
from langchain.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain_core.documents.base import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import chain
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter

from extractive_summary import (
    EmbeddingModel,
    build_text_prompt,
    build_text_prompt_kmeans,
)

summarize_template = """
Write a summary of the following text:
{text}
SUMMARY :
"""

summarize_prompt = PromptTemplate.from_template(summarize_template)

map_template = """The following is a set of documents
{docs}
Based on this list of docs, please identify the main themes
Helpful Answer:"""
map_prompt = PromptTemplate.from_template(map_template)

reduce_template = """The following is set of summaries
{docs}
Take these and distill it into a final, consolidated summary written of the
main themes.
Helpful Answer:"""
reduce_prompt = PromptTemplate.from_template(reduce_template)

question_prompt_template = """Write a concise summary of the following :
{text}
CONCISE SUMMARY:"""
question_prompt = PromptTemplate.from_template(question_prompt_template)
refine_template = (
    """Your job is to produce a final summary\n"
    "We have provided an existing summary up to a certain point:
    {existing_answer}\n"
    "We have the opportunity to refine the existing summary"
    "(only if needed) with some more context below.\n"
    "------------\n"
    "{text}\n"
    "------------\n"
    "Given the new context, refine the original summary in Italian"
    "If the context isn't useful, return the original summary."""
)
refine_prompt = PromptTemplate.from_template(refine_template)


MethodType = Literal["text_rank", "map_reduce", "refine", "k-means", "stuff"]


def summarize_chain_builder(
    llm=None,
    llm_context_window_size: int = 3000,
    embedding_model: EmbeddingModel = None,
    language: str = "English",
    method: MethodType = "text_rank",
    **kwargs,
):
    """Build a custom summarizing chain with your models, using the selected
    method for summarization

    Parameters
    -----------
    llm: Any = None
        chat model that will be tasked to execute the abstractive summary
        default to miom api if None
    llm_context_window_size : int = 5000
        context window size (in terms of len(text), not tokens) for which the
        llm can best exploit the context
    embedding_model: Model = None
        model chosen for embeddings, please use an instance of EmbeddingModel
        it with the custom class Model
        default to miom api if None
    language : str = "French"
        language to use to write the summary
    method : Literal['text_rank', 'map_reduce', 'refine', 'k-means']
        method to build the summary
        default to text_rank

    Returns
    ----------
    Runnable[Any, str]
        custom chain that can be invoked to summarize text
    """

    if llm is None or embedding_model is None:
        load_dotenv()
        OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
        OPENAI_API_BASE = os.environ["OPENAI_API_BASE"]
        OPENAI_EMBEDDING_API_KEY = os.environ["OPENAI_EMBEDDING_API_KEY"]
        OPENAI_EMBEDDING_API_BASE = os.environ["OPENAI_EMBEDDING_API_BASE"]

    if llm is None:
        llm = ChatOpenAI(
            api_key=OPENAI_API_KEY, openai_api_base=OPENAI_API_BASE
        )

    if embedding_model is None:
        openai_ef = OpenAIEmbeddingFunction(
            api_key=OPENAI_EMBEDDING_API_KEY,
            api_base=OPENAI_EMBEDDING_API_BASE,
        )
        embedding_model = EmbeddingModel(openai_ef, "OpenAIEmbeddingFunction")

    match method:
        case "text_rank":

            @chain
            def custom_chain(text):
                extractive_summary = build_text_prompt(
                    text, llm_context_window_size, embedding_model, **kwargs
                )
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

                text_splitter = (
                    RecursiveCharacterTextSplitter.from_tiktoken_encoder(
                        chunk_size=1000, chunk_overlap=0
                    )
                )
                split_texts = text_splitter.split_text(text)
                split_docs = []
                for text in split_texts:
                    split_docs.append(Document(page_content=text))
                result = refine_chain.invoke(
                    {"input_documents": split_docs}, return_only_outputs=True
                )
                return result["output_text"]

        case "map_reduce":

            @chain
            def custom_chain(text):
                map_chain = LLMChain(llm=llm, prompt=map_prompt)
                reduce_chain = LLMChain(llm=llm, prompt=reduce_prompt)
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
                text_splitter = (
                    RecursiveCharacterTextSplitter.from_tiktoken_encoder(
                        chunk_size=4000, chunk_overlap=0
                    )
                )
                split_text = text_splitter.split_text(text)
                split_docs = []
                for text in split_text:
                    split_docs.append(Document(page_content=text))
                result = map_reduce_chain.invoke(split_docs)
                return result["output_text"]

        case "k-means":

            @chain
            def custom_chain(text: str):
                extractive_summary = build_text_prompt_kmeans(
                    text, llm_context_window_size, embedding_model, **kwargs
                )
                prompt1 = summarize_prompt.invoke({"text": extractive_summary})
                output = llm.invoke(prompt1)
                output_parser = StrOutputParser()
                return output_parser.invoke(output)

        case "stuff":

            @chain
            def custom_chain(text: str):
                llm_chain = LLMChain(llm=llm, prompt=summarize_prompt)
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

    # Chain bifurcation for smaller text
    @chain
    def small_text_handler_chain(text: str):
        if llm.get_num_tokens(text) < 3000:
            prompt = summarize_prompt.invoke(
                {"text": text, "language": language}
            )
            output = llm.invoke(prompt)
            output_parser = StrOutputParser()
            return output_parser.invoke(output)
        else:
            return custom_chain.invoke(text)

    # Translation chain
    @chain
    def translation_chain(text: str):
        if language == "English":
            return small_text_handler_chain.invoke(text)
        else:
            english_summary = small_text_handler_chain.invoke(text)

            # Translation by Antonio
            template = """You are a helpful assistant that translates
            {input_language} to {output_language}."""
            system_message_prompt = SystemMessagePromptTemplate.from_template(
                template
            )
            human_template = """Translate this sentence from {input_language}
            to {output_language}. {text}"""
            human_message_prompt = HumanMessagePromptTemplate.from_template(
                human_template
            )

            chat_promt = ChatPromptTemplate.from_messages(
                [system_message_prompt, human_message_prompt]
            )

            summary = llm.invoke(
                chat_promt.format_prompt(
                    input_language="English",
                    output_language=language,
                    text=english_summary,
                ).to_messages()
            )

            output_parser = StrOutputParser()
            return output_parser.invoke(summary)

    return translation_chain
