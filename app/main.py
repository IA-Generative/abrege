import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Literal
from urllib.parse import urlparse

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
from pypdf import PdfReader
from abrege.extractive_summary import EmbeddingModel
from abrege.summary_chain import summarize_chain_builder


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

    model_class = "HuggingFaceEmbeddings"
    embedding_model = EmbeddingModel(embeddings, model_class)

    OPENAI_API_BASE = os.environ["OPENAI_API_BASE"]
    OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

    llm = ChatOpenAI(
        api_key=OPENAI_API_KEY,
        openai_api_base=OPENAI_API_BASE,
        temperature=0,
        model="mixtral",
    )

    custom_chain = summarize_chain_builder(
        method="text_rank", embedding_model=embedding_model, llm=llm
    )

    context["chain"] = custom_chain

    context["llm"] = llm

    context["embedding_model"] = embedding_model

    logger.info("======== Lifespan initialization done =========")

    yield
    # Clean up the resources
    context.clear()


logger = logging.getLogger()

description = (Path(__file__).parent.parent / "README.md").read_text()

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


@app.get("/healthcheck", status_code=200)
async def healthcheck():
    return


MethodType = Literal["map_reduce", "refine", "text_rank", "k-means"]
ChunkType = Literal["sentences", "chunks"]


@app.get("/url/{url}")
def summarize_url(url: str, method: MethodType = "text_rank"):

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


@app.post("/doc")
async def summarize_doc(file: UploadFile, method: MethodType = "text_rank"):
    """This route is for single file only"""

    if file.filename is not None:
        extension = file.filename.split(".")[-1]
    else:
        raise HTTPException(
            status_code=400,
            detail="No extension found on upload file",
        )

    if extension not in {"pdf", "txt"}:
        raise HTTPException(
            status_code=400,
            detail="""file format not supported, file format supported are :
              [pdf, txt]""",
        )

    if extension == "pdf":
        text = ""
        reader = PdfReader(file.file)
        for page in reader.pages:
            text += page.extract_text()

    elif extension == "txt":
        text = await file.read()
        text = text.decode()

    if method != "k-means":
        custom_chain = summarize_chain_builder(
            llm=context["llm"],
            embedding_model=context["embedding_model"],
            method=method,
        )
    else:
        custom_chain = context["chain"]

    res = custom_chain.invoke(text)

    return {"summary": res}


@app.post("/docs")
async def summarize_multi_doc(
    files: List[UploadFile],
    method: MethodType = "k-means",
    one_summary: bool = False,
):
    """Route for multiple files"""

    summaries = []
    for file in files:
        file_summary = await summarize_doc(file, method)
        summaries.append(file_summary)

    if one_summary:
        custom_chain = summarize_chain_builder(
            llm=context["llm"],
            embedding_model=context["embedding_model"],
            method="stuff",
        )
        docs = []
        for summary in summaries:
            docs.append(Document(page_content=summary))

        summaries = [custom_chain.invoke(docs)]

    return {"summaries": summaries}


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
