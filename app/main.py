import os, sys, logging, random, asyncio, uvicorn, time
from typing import Union
import logging
from typing import Literal
import os
import sys
import json
import time
import re
from contextlib import asynccontextmanager
from pathlib import Path
from datetime import datetime
from collections import Counter
from typing import Dict, List
from urllib.parse import urlparse, urlsplit

from fastapi import FastAPI, HTTPException, status, Security, UploadFile
from fastapi.security.api_key import APIKeyHeader
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from langchain.chains.question_answering import load_qa_chain
from langchain_community.vectorstores.chroma import Chroma
from langchain_openai import ChatOpenAI
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

from fastapi import FastAPI

sys.path.append("../src")
from summary_chain import summarize_chain_builder, EmbeddingModel

import nltk

nltk.download("punkt")


origins = [
    "https://sie.numerique-interieur.com",
    "http://localhost",
    "http://localhost:8080",
]

logger = logging.getLogger(__name__)
context = {}


@asynccontextmanager
async def lifespan(_: FastAPI):
    """
    Load the resources used by the API (models, data)
    """
    load_dotenv()

    embeddings = HuggingFaceEmbeddings(
        model_name=os.environ["EMBEDDING_MODEL_PATH"]
    )  # plus de 13 min
    logger.info(f"Embedding model {repr(embeddings)} available")

    embedding_model = EmbeddingModel(embeddings, "HuggingFaceEmbeddings")

    OPENAI_API_BASE = os.environ["OPENAI_API_BASE"]
    OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

    llm = ChatOpenAI(
        api_key=OPENAI_API_KEY,
        openai_api_base=OPENAI_API_BASE,
        temperature=0,
        model="mixtral",
    )

    custom_chain = summarize_chain_builder(
        method="k-means", embedding_model=embedding_model, llm=llm
    )

    context["chain"] = custom_chain

    context["llm"] = llm

    context["embedding_model"] = embedding_model

    logger.info("======== Lifespan initialization done =========")

    yield
    # Clean up the resources
    context.clear()


logger = logging.getLogger()

description = Path("../README.md").read_text()


API_KEY_HEADER = APIKeyHeader(name="x-api-key", auto_error=False)

app = FastAPI(
    title="abrege", description=description, version="0.0.1", lifespan=lifespan
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", status_code=200)
async def healthcheck():
    return "Hello"


@app.get("/healthcheck", status_code=200)
async def healthcheck():
    return


@app.get("/camus")
def read_item(url: str):
    text2 = Path("./data/camus.txt").read_text()
    res = context["chain"].invoke(text2)
    return res


MethodType = Literal["map_reduce", "refine", "text_rank", "k-means"]
ChunkType = Literal["sentences", "chunks"]


@app.get("/url/{url}")
def summarize_url(url: str, method: MethodType = "k-means"):

    if method is None:
        custom_chain = context["chain"]
    else:
        custom_chain = summarize_chain_builder(
            llm=context["chain"],
            embedding_model=context["embedding_model"],
            method=method,
        )

    parsed_url = urlparse(url)
    if not (parsed_url.scheme and parsed_url.netloc):
        url = "https://www.jesuismort.com/tombe/albert-camus"

    if 1:
        from langchain_community.document_loaders import UnstructuredURLLoader

        loader = UnstructuredURLLoader(urls=[url])
    else:
        from langchain_community.document_loaders import SeleniumURLLoader

        loader = SeleniumURLLoader(urls=[url])
    data: list = loader.load()

    res = [custom_chain.invoke(doc.page_content) for doc in data]

    return "\n\n".join(res)


@app.get("/text_summary")
def summarize_text(text: str, method: MethodType = "k-means"):

    if method is None:
        res = [context["chain"].invoke(text)]

    else:
        custom_chain = summarize_chain_builder(
            llm=context["llm"],
            embedding_model=context["embedding_model"],
            method=method,
        )
        res = [custom_chain.invoke(text)]

    return "\n\n".join(res)


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
