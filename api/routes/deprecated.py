from utils.pdf_handler import ModeOCR, OCRPdfLoader
from typing import Annotated, get_args
import requests
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse
import tempfile
import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader
from fastapi.responses import StreamingResponse
from openai import OpenAI
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain_community.document_loaders import (
    PyPDFLoader,
    UnstructuredODTLoader,
    Docx2txtLoader,
    UnstructuredURLLoader,
    TextLoader,
)

from abrege.summary_chain import (
    summarize_chain_builder,
    EmbeddingModel,
    prompt_template,
)
import sys
import nltk
from models.chat import chat_builder
from utils.url_parser import url_scrapper
from fastapi import APIRouter


MethodType = Literal[
    "map_reduce", "refine", "text_rank", "k-means", "stuff"
]  # "text_rank2", "k-means2"
ChunkType = Literal["sentences", "chunks"]

DOCUMENT_LOADER_DICT = {
    ".pdf": PyPDFLoader,
    ".docx": Docx2txtLoader,
    ".odt": UnstructuredODTLoader,
    ".txt": TextLoader,
}

DEFAULT_MODEL = "summary"
DEFAULT_METHOD = "map_reduce"
OPENAI_API_BASE = os.environ.get("OPENAI_API_BASE", "http://localhost")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", 'http://localhost')
OPENAI_EMBEDDING_API_KEY = os.environ.get(
    "OPENAI_EMBEDDING_API_KEY", "http://localhost")
OPENAI_EMBEDDING_API_BASE = os.environ.get(
    "OPENAI_EMBEDDING_API_BASE", "http://localhost")
PADDLE_OCR_TOKEN = os.environ.get("PADDLE_OCR_TOKEN")
PADDLE_OCR_URL = os.environ.get("PADDLE_OCR_URL")
context = {}

router = APIRouter()


@router.get("/url")
def summarize_url(
    url: str,
    method: MethodType = "map_reduce",
    model: str = DEFAULT_MODEL,
    context_size: int = None,
    temperature: Annotated[float, Query(ge=0, le=1.0)] = 0,
    language: str = None,
    size: int = None,
    summarize_template: str | None = None,
    map_template: str | None = None,
    reduce_template: str | None = None,
    question_template: str | None = None,
    refine_template: str | None = None,
    custom_prompt: str | None = None,
):
    """Generate a summary of text found by resolving the url

    Parameters
    ----------
    url : str
        url to fetch to retrieve text
    method : MethodType, optional
        method to use to generate the summary, by default "text_rank"
    model : str, optional
        llm to use, by default "phi3"
    context_size: int
        maximum size of the context windows passed to the llm
        bigger size allows more context but also induces more mistakes by the llm
        default to 10_000
    temperature : Annotated[float, Query, optional
        temperature parameter of the llm, by default 0, le=1.0)]=0
    language : str, optional
        language to use to write the summary, by default "English"
    size : int
        size of the final summary, in words
        default to 200
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
    -------
    dict[str, str]
        summary
    """

    llm = chat_builder(openai_key=OPENAI_API_KEY, openai_api_base=OPENAI_API_BASE,
                       model=model,  model_id=context["models"], temperature=temperature)
    custom_chain = summarize_chain_builder(
        llm=llm,
        embedding_model=context["embedding_model"],
        method=method,
        context_size=context_size,
        language=language,
        size=size,
        summarize_template=summarize_template,
        map_template=map_template,
        reduce_template=reduce_template,
        question_template=question_template,
        refine_template=refine_template,
        custom_prompt=custom_prompt,
    )

    data = url_scrapper(url=url)

    res = [custom_chain.invoke({"text": doc.page_content}) for doc in data]

    res = "\n\n".join(res).strip()
    return {"summary": res}


@router.get("/text")
async def summarize_txt(
    text: str,
    method: MethodType = DEFAULT_METHOD,
    model: str = DEFAULT_MODEL,
    context_size: int = None,
    temperature: Annotated[float, Query(ge=0, le=1.0)] = 0,
    language: str = None,
    size: int = None,
    summarize_template: str | None = None,
    map_template: str | None = None,
    reduce_template: str | None = None,
    question_template: str | None = None,
    refine_template: str | None = None,
    custom_prompt: str | None = None,
):
    """Generate a summary of the raw text

    Parameters
    ----------
    text : str
        text to summarize
    method : MethodType, optional
        method to use to generate the summary, by default "text_rank"
    model : str, optional
        llm to use, by default "phi3"
    context_size: int
        maximum size of the context windows passed to the llm
        bigger size allows more context but also induces more mistakes by the llm
        default to 10_000
    temperature : Annotated[float, Query, optional
        temperature parameter of the llm, by default 0, le=1.0)]=0
    language : str, optional
        language to use to write the summary, by default "English"
    size : int
        size of the final summary, in words
        default to 200
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
    -------
    dict[str, str]
        summary
    """
    from time import perf_counter

    # logger.warning(f"{len(text)=}")
    llm = context["chat_builder"](model, temperature)
    custom_chain = summarize_chain_builder(
        llm=llm,
        embedding_model=context["embedding_model"],
        method=method,
        context_size=context_size,
        language=language,
        size=size,
        summarize_template=summarize_template,
        map_template=map_template,
        reduce_template=reduce_template,
        question_template=question_template,
        refine_template=refine_template,
        custom_prompt=custom_prompt,
    )

    deb = perf_counter()

    res = custom_chain.invoke({"text": text})

    elapsed = perf_counter() - deb

    return {"summary": res, "time": elapsed}


@router.post("/doc")
async def summarize_doc(
    file: UploadFile,
    method: MethodType = DEFAULT_METHOD,
    pdf_mode_ocr: ModeOCR | None = None,
    model: str = DEFAULT_MODEL,
    context_size: int = None,
    temperature: Annotated[float, Query(ge=0, le=1.0)] = 0,
    language: str = None,
    size: int = None,
    summarize_template: str | None = None,
    map_template: str | None = None,
    reduce_template: str | None = None,
    question_template: str | None = None,
    refine_template: str | None = None,
    custom_prompt: str | None = None,
):
    """Generate a summary of the file

    Parameters
    ----------
    file : UploadFile
        file to generate a summary from it's content
    method : MethodType, optional
        method to use to generate the summary, by default "text_rank"
    model : str, optional
        llm to use, by default "phi3"
    context_size: int
        maximum size of the context windows passed to the llm
        bigger size allows more context but also induces more mistakes by the llm
        default to 10_000
    temperature : Annotated[float, Query, optional
        temperature parameter of the llm, by default 0, le=1.0)]=0
    language : str, optional
        language to use to write the summary, by default "English"
    size : int
        size of the final summary, in words
        default to 200
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
    -------
    dict[str, str]
        summary
    """

    llm = context["chat_builder"](model, temperature)

    custom_chain = summarize_chain_builder(
        llm=llm,
        embedding_model=context["embedding_model"],
        method=method,
        context_size=context_size,
        language=language,
        size=size,
        summarize_template=summarize_template,
        map_template=map_template,
        reduce_template=reduce_template,
        question_template=question_template,
        refine_template=refine_template,
        custom_prompt=custom_prompt,
    )

    if file.filename is not None:
        try:
            _, extension = os.path.splitext(file.filename)
        except Exception as err:
            raise HTTPException(
                status_code=422,
                detail=f"""Error while parsing the filename, {err} occured""",
            )

    if extension not in DOCUMENT_LOADER_DICT:
        raise HTTPException(
            status_code=422,
            detail=f"""file format not supported, file format supported are :
              {tuple(DOCUMENT_LOADER_DICT.keys())}""",
        )

    if extension == ".pdf" and pdf_mode_ocr is None:
        raise HTTPException(
            status_code=422,
            detail=f"""for pdf files, the pdf_mode_ocr parameter must be specified
            ({repr(tuple(ModeOCR.__args__))})""",
        )

    # Dirty method required: save content to a tempory file and read it...
    with tempfile.NamedTemporaryFile(mode="w+b") as tmp_file:
        tmp_file.write(file.file.read())
        if extension != ".pdf" or pdf_mode_ocr == "full_text":
            loader = DOCUMENT_LOADER_DICT[extension](tmp_file.name)
            docs = loader.load()
        else:
            loader = OCRPdfLoader(tmp_file.name)
            docs = loader.load(mode=pdf_mode_ocr)

    text = "\n".join(doc.page_content for doc in docs)

    if len(text) < size:
        raise HTTPException(
            status_code=422, detail="Text retrieved from documents too short"
        )

    res = custom_chain.invoke({"text": text})
    res = res.strip()

    return {"summary": res}


@router.get("/models")
async def list_model():
    """Get a list a available mode for the api"""
    return context["models"]


@router.get("/default_params")
async def param():
    """Generate a dict of default param of the app
    Return the available models, available methods and default prompt_template"""
    return {
        "models": context["models"],
        "methods": get_args(MethodType),
        "prompt_template": prompt_template,
    }


@router.get("/text_stream")
async def stream_summary(
    text: str,
    method: MethodType = DEFAULT_METHOD,
    model: str = DEFAULT_MODEL,
    context_size: int = None,
    temperature: Annotated[float, Query(ge=0, le=1.0)] = 0,
    language: str = None,
    size: int = None,
    summarize_template: str | None = None,
    map_template: str | None = None,
    reduce_template: str | None = None,
    question_template: str | None = None,
    refine_template: str | None = None,
    custom_prompt: str | None = None,
):
    """Generate a summary of the raw text

    Parameters
    ----------
    text : str
        text to summarize
    method : MethodType, optional
        method to use to generate the summary, by default "text_rank"
    model : str, optional
        llm to use, by default "phi3"
    context_size: int
        maximum size of the context windows passed to the llm
        bigger size allows more context but also induces more mistakes by the llm
        default to 10_000
    temperature : Annotated[float, Query, optional
        temperature parameter of the llm, by default 0, le=1.0)]=0
    language : str, optional
        language to use to write the summary, by default "English"
    size : int
        size of the final summary, in words
        default to 200
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
    -------
    dict[str, str]
        summary
    """
    llm = context["chat_builder"](model, temperature)
    custom_chain = summarize_chain_builder(
        llm=llm,
        embedding_model=context["embedding_model"],
        method=method,
        context_size=context_size,
        language=language,
        size=size,
        summarize_template=summarize_template,
        map_template=map_template,
        reduce_template=reduce_template,
        question_template=question_template,
        refine_template=refine_template,
        custom_prompt=custom_prompt,
    )

    return StreamingResponse(custom_chain.astream({"text": text}))


@router.post("/doc_stream")
async def summarize_doc_stream(
    file: UploadFile,
    method: MethodType = DEFAULT_METHOD,
    pdf_mode_ocr: ModeOCR | None = None,
    model: str = DEFAULT_MODEL,
    context_size: int | None = None,
    temperature: Annotated[float, Query(ge=0, le=1.0)] = 0,
    language: str | None = None,
    size: int | None = None,
    summarize_template: str | None = None,
    map_template: str | None = None,
    reduce_template: str | None = None,
    question_template: str | None = None,
    refine_template: str | None = None,
    custom_prompt: str | None = None,
):
    """Generate a summary of the file

    Parameters
    ----------
    file : UploadFile
        file to generate a summary from it's content
    method : MethodType, optional
        method to use to generate the summary, by default "text_rank"
    model : str, optional
        llm to use, by default "phi3"
    context_size: int
        maximum size of the context windows passed to the llm
        bigger size allows more context but also induces more mistakes by the llm
        default to 10_000
    temperature : Annotated[float, Query, optional
        temperature parameter of the llm, by default 0, le=1.0)]=0
    language : str, optional
        language to use to write the summary, by default "English"
    size : int
        size of the final summary, in words
        default to 200
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
    -------
    dict[str, str]
        summary
    """

    llm = context["chat_builder"](model, temperature)

    custom_chain = summarize_chain_builder(
        llm=llm,
        embedding_model=context["embedding_model"],
        method=method,
        context_size=context_size,
        language=language,
        size=size,
        summarize_template=summarize_template,
        map_template=map_template,
        reduce_template=reduce_template,
        question_template=question_template,
        refine_template=refine_template,
        custom_prompt=custom_prompt,
    )

    if file.filename is not None:
        try:
            _, extension = os.path.splitext(file.filename)
        except Exception as err:
            raise HTTPException(
                status_code=422,
                detail=f"""Error while parsing the filename, {err} occured""",
            )

    if extension not in DOCUMENT_LOADER_DICT:
        raise HTTPException(
            status_code=422,
            detail=f"""file format not supported, file format supported are :
              {tuple(DOCUMENT_LOADER_DICT.keys())}""",
        )

    if extension == ".pdf" and pdf_mode_ocr is None:
        raise HTTPException(
            status_code=422,
            detail=f"""for pdf files, the pdf_mode_ocr parameter must be specified
            ({repr(tuple(ModeOCR.__args__))})""",
        )

    # Dirty method required: save content to a tempory file and read it...
    with tempfile.NamedTemporaryFile(mode="w+b") as tmp_file:
        tmp_file.write(file.file.read())
        if extension != ".pdf" or pdf_mode_ocr == "full_text":
            loader = DOCUMENT_LOADER_DICT[extension](tmp_file.name)
            docs = loader.load()
        else:
            loader = OCRPdfLoader(tmp_file.name)
            docs = loader.load(mode=pdf_mode_ocr)

    text = "\n".join(doc.page_content for doc in docs)

    if len(text) < size:
        raise HTTPException(
            status_code=422, detail="Text retrieved from documents too short"
        )

    return StreamingResponse(custom_chain.astream({"text": text}))
