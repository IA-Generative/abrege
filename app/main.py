import tempfile
import logging
import os
import requests
import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Literal, Annotated
from urllib.parse import urlparse

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
from langchain_community.document_loaders import (
    PyPDFLoader,
    UnstructuredODTLoader,
    Docx2txtLoader,
)
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
    OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
    OPENAI_API_BASE = os.environ["OPENAI_API_BASE"]
    MODEL_LIST_BASE = os.environ["MODEL_LIST_BASE"]

    # Load the models
    header = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    response = requests.get(MODEL_LIST_BASE, headers=header)

    if response.status_code == 200:
        models_list = json.loads(response.text)["data"]
        model_id = [model["id"] for model in models_list]
        context["models"] = model_id
    else:
        raise ValueError(
            f"""Models list not availble, error status code : {response.status_code},
            reason: {response.text}"""
        )

    embeddings = HuggingFaceEmbeddings(
        model_name=os.environ["EMBEDDING_MODEL_PATH"]
    )  # plus de 13 min
    logger.info(f"Embedding model {repr(embeddings)} available")

    model_class = "HuggingFaceEmbeddings"
    embedding_model = EmbeddingModel(embeddings, model_class)

    def chat_builder(model: str = "mixtral", temperature: int = 0):
        if model not in model_id:
            raise HTTPException(
                400, detail=f"Model not available, avaible are {model_id}"
            )
        llm = ChatOpenAI(
            api_key=OPENAI_API_KEY,
            openai_api_base=OPENAI_API_BASE,
            model=model,
            temperature=temperature,
        )
        return llm

    context["chat_builder"] = chat_builder

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
def summarize_url(
    url: str,
    method: MethodType = "text_rank",
    model: str = "mixtral",
    temperature: Annotated[float, Query(ge=0, le=1.0)] = 0,
    language: str = "English",
    prompt_template: str | None = None,
):
    """Generate a summary of text found by resolving the url

    Parameters
    ----------
    url : str
        url to fetch to retrieve text
    method : MethodType, optional
        method to use to generate the summary, by default "text_rank"
    model : str, optional
        llm to use, by default "mixtral"
    temperature : Annotated[float, Query, optional
        temperature parameter of the llm, by default 0, le=1.0)]=0
    language : str, optional
        language to use to write the summary, by default "English"
    prompt_template : str | None, optional
        prompt template used to ask for a summary, should contain a '{text}'
        by default None, will result to a basic summary prompt

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
        language=language,
        summary_template=prompt_template,
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


@app.get("/txt")
async def summarize_txt(
    text: str,
    method: MethodType = "text_rank",
    model: str = "mixtral",
    temperature: Annotated[float, Query(ge=0, le=1.0)] = 0,
    language: str = "English",
    prompt_template: str | None = None,
):
    """Generate a summary of the raw text

    Parameters
    ----------
    text : str
        text to summarize
    method : MethodType, optional
        method to use to generate the summary, by default "text_rank"
    model : str, optional
        llm to use, by default "mixtral"
    temperature : Annotated[float, Query, optional
        temperature parameter of the llm, by default 0, le=1.0)]=0
    language : str, optional
        language to use to write the summary, by default "English"
    prompt_template : str | None, optional
        prompt template used to ask for a summary, should contain a '{text}'
        by default None, will result to a basic summary prompt

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
        language=language,
        summary_template=prompt_template,
    )

    res = custom_chain.invoke(text)

    return {"summary": res}


@app.post("/doc")
async def summarize_doc(
    file: UploadFile,
    method: MethodType = "text_rank",
    model: str = "mixtral",
    temperature: Annotated[float, Query(ge=0, le=1.0)] = 0,
    language: str = "English",
    prompt_template: str | None = None,
):
    """Generate a summary of the file

    Parameters
    ----------
    file : UploadFile
        file to generate a summary from it's content
    method : MethodType, optional
        method to use to generate the summary, by default "text_rank"
    model : str, optional
        llm to use, by default "mixtral"
    temperature : Annotated[float, Query, optional
        temperature parameter of the llm, by default 0, le=1.0)]=0
    language : str, optional
        language to use to write the summary, by default "English"
    prompt_template : str | None, optional
        prompt template used to ask for a summary, should contain a '{text}'
        by default None, will result to a basic summary prompt

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
        language=language,
        summary_template=prompt_template,
    )

    if file.filename is not None:
        try:
            _, extension = os.path.splitext(file.filename)
        except Exception as err:
            raise HTTPException(
                status_code=400,
                detail=f"""Error while parsing the filename, {err} occured""",
            )

    if extension not in {".pdf", ".odt", ".docx"}:
        raise HTTPException(
            status_code=400,
            detail="""file format not supported, file format supported are :
              [pdf, docx, odt]""",
        )

    # Dirty method required: save content to a tempory file and read it...
    with tempfile.NamedTemporaryFile(mode="w+b") as tmp_file:
        tmp_file.write(file.file.read())

        if extension == ".pdf":
            loader = PyPDFLoader(tmp_file.name)

        elif extension == ".docx":
            loader = Docx2txtLoader(tmp_file.name)

        elif extension == ".odt":
            loader = UnstructuredODTLoader(tmp_file.name)

        docs = loader.load()
        text = "".join([doc.page_content for doc in docs])

    res = custom_chain.invoke(text)

    return {"summary": res}


@app.post("/docs")
async def summarize_multi_doc(
    files: List[UploadFile],
    method: MethodType = "k-means",
    model: str = "mixtral",
    one_summary: bool = False,
    temperature: Annotated[float, Query(ge=0, le=1.0)] = 0,
    language: str = "English",
    prompt_template: str | None = None,
):

    summaries = []
    for file in files:
        file_summary = await summarize_doc(file, method, model, temperature)
        summaries.append(file_summary)

    if one_summary:
        llm = context["chat_builder"](model, temperature)
        custom_chain = summarize_chain_builder(
            llm=llm,
            embedding_model=context["embedding_model"],
            method="stuff",
            language=language,
            summary_template=prompt_template,
        )
        docs = []
        for summary in summaries:
            docs.append(Document(page_content=summary))

        summaries = [custom_chain.invoke(docs)]

    return {"summaries": summaries}


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
