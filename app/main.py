from typing import Annotated
import requests
import json
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Literal
from urllib.parse import urlparse
import tempfile
import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
from langchain_community.document_loaders import (
    PyPDFLoader,
    UnstructuredODTLoader,
    Docx2txtLoader,
    UnstructuredURLLoader,
    # SeleniumURLLoader
)
from abrege.summary_chain import summarize_chain_builder, EmbeddingModel


DOCUMENT_LOADER_DICT = {
    ".pdf": PyPDFLoader,
    ".docx": Docx2txtLoader,
    ".odt": UnstructuredODTLoader,
}

origins = (
    "https://sie.numerique-interieur.com",
    "http://localhost",
    "http://localhost:8080",
)
logger = logging.getLogger("uvicorn.error")
context = {}


@asynccontextmanager
async def lifespan(_: FastAPI):
    """
    Load the resources used by the API (models, data)
    """
    error_flag = 0
    # if 0:
    #     embeddings = HuggingFaceEmbeddings(
    #         model_name=os.environ["EMBEDDING_MODEL_PATH"]
    #     )  # plus de 13 min
    #     logger.info(f"Embedding model {repr(embeddings)} available")

    #     model_class = "HuggingFaceEmbeddings"
    #     embedding_model = EmbeddingModel(embeddings, model_class)

    OPENAI_API_BASE = os.environ.get("OPENAI_API_BASE")
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    MODEL_LIST_BASE = os.environ.get("MODEL_LIST_BASE")
    OPENAI_EMBEDDDING_KEY = os.environ.get("OPENAI_EMBEDDING_API_KEY")
    OPENAI_EMBEDDING_BASE = os.environ.get("OPENAI_EMBEDDING_API_BASE")

    if all(
        (
            MODEL_LIST_BASE,
            OPENAI_API_BASE,
            OPENAI_API_KEY,
            OPENAI_EMBEDDDING_KEY,
            OPENAI_EMBEDDING_BASE,
        )
    ):
        # Load the models
        header = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
        response = requests.get(MODEL_LIST_BASE, headers=header)

        if response.status_code == 200:
            models_list = json.loads(response.text)["data"]
            model_id = [model["id"] for model in models_list]
            logger.info(f"Model available : {model_id}")
            context["models"] = model_id

            def chat_builder(model: str = "vicuna", temperature: int = 0):
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

            embedding_model = OpenAIEmbeddingFunction(
                api_key=OPENAI_EMBEDDDING_KEY, api_base=OPENAI_EMBEDDING_BASE
            )
            embedding_model = EmbeddingModel(embedding_model)
            context["embedding_model"] = embedding_model
        else:

            logger.critical(
                f"""Models list not availble, error status code :
                {response.status_code}, reason: {response.text}"""
            )

            # For test without environnement variable
            def none_func(*args, **kwargs):
                pass

            context["chat_builder"] = none_func
            context["embedding_model"] = None
            error_flag = 1

    else:
        logger.critical("Problem loading environnement variable")

        # To ensure test pass
        def none_func(*args, **kwargs):
            pass

        context["chat_builder"] = none_func
        error_flag = 1

    if not error_flag:
        logger.info("======== Lifespan initialization done =========")
    else:
        logger.error(
            """Application startup has encoutered a problem and is not stable
Please check the log and restart the application"""
        )

    yield
    # Clean up the resources
    context.clear()


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


MethodType = Literal[
    "map_reduce", "refine", "text_rank", "k-means", "text_rank2", "stuff", "k-means2"
]
ChunkType = Literal["sentences", "chunks"]


@app.get("/url")
def summarize_url(
    url: str,
    method: MethodType = "text_rank",
    model: str = "vicuna",
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
        llm to use, by default "vicuna"
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
        prompt_template=prompt_template,
    )

    parsed_url = urlparse(url)
    if not (parsed_url.scheme and parsed_url.netloc):
        raise HTTPException(
            status_code=400,
            detail=f"""{url} is not a valid url""",
        )

    loader = UnstructuredURLLoader(urls=[url])
    data: list = loader.load()

    res = [custom_chain.invoke(doc.page_content) for doc in data]

    return "\n\n".join(res).strip()


@app.get("/text")
async def summarize_txt(
    text: str,
    method: MethodType = "text_rank",
    model: str = "vicuna",
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
        llm to use, by default "vicuna"
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
        prompt_template=prompt_template,
    )

    res = custom_chain.invoke(text)

    return {"summary": res}


@app.post("/doc")
async def summarize_doc(
    file: UploadFile,
    method: MethodType = "text_rank",
    model: str = "vicuna",
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
        llm to use, by default "vicuna"
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
        prompt_template=prompt_template,
    )

    if file.filename is not None:
        try:
            _, extension = os.path.splitext(file.filename)
        except Exception as err:
            raise HTTPException(
                status_code=400,
                detail=f"""Error while parsing the filename, {err} occured""",
            )

    if extension not in DOCUMENT_LOADER_DICT:
        raise HTTPException(
            status_code=400,
            detail=f"""file format not supported, file format supported are :
              {tuple(DOCUMENT_LOADER_DICT.keys())}""",
        )

    # Dirty method required: save content to a tempory file and read it...
    with tempfile.NamedTemporaryFile(mode="w+b") as tmp_file:
        tmp_file.write(file.file.read())
        loader = DOCUMENT_LOADER_DICT[extension](tmp_file.name)
        docs = loader.load()

    text = "".join(doc.page_content for doc in docs)

    res = custom_chain.invoke(text).strip()

    return {"summary": res}


@app.post("/docs")
async def summarize_multi_doc(
    files: List[UploadFile],
    method: MethodType = "k-means",
    model: str = "vicuna",
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
            prompt_template=prompt_template,
        )
        docs = [Document(page_content=summary) for summary in summaries]
        summaries = [custom_chain.invoke(docs)]

    return {"summaries": summaries}


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
