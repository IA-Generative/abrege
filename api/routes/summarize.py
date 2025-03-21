import os
from typing import get_args
from openai import OpenAI
from fastapi import HTTPException, UploadFile, APIRouter
from models.naive import process_documents
from schemas.params import MethodType
from prompt.template import prompt_template
from utils.url_parser import url_scrapper
from utils.pdf_handler import ModeOCR
from utils.parse import parse_files
from config.openai import OpenAISettings

client = OpenAI(api_key=OpenAISettings().OPENAI_API_KEY,
                base_url=OpenAISettings().OPENAI_API_BASE)
models_available = [model.id for model in client.models.list().data]

context = {}

router = APIRouter()


@router.post("/url")
async def summarize_url(url: str, model: str):
    if model not in models_available:
        raise HTTPException(
            status_code=500, detail=f"{model} not Found {models_available}")
    data = url_scrapper(url=url)
    docs = [doc.page_content for doc in data]

    return process_documents(docs=docs, model=model, client=client)


@router.get("/url", deprecated=True)
async def get_summarize_url(url: str, model: str = "chat-leger"):
    try:

        return await summarize_url(url=url, model=model)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/text")
async def summarize_txt(
    text: str,
    model: str
):
    return process_documents(docs=[text], model=model, client=client)


@router.get("/text", deprecated=True)
async def get_summarize_txt(
    text: str,
    model: str
):
    return await summarize_txt(text=text, model=model)


@router.post("/doc")
async def summarize_doc(
    file: UploadFile,
    model: str,
    pdf_mode_ocr: ModeOCR | None = None,


):
    docs = parse_files(file=file, pdf_mode_ocr=pdf_mode_ocr)

    return process_documents(docs=docs, model=model, client=client)


@router.get("/models")
async def list_model():
    """Get a list a available mode for the api"""
    return models_available


@router.get("/default_params")
async def param():
    """Generate a dict of default param of the app
    Return the available models, available methods and default prompt_template"""
    return {
        "models": models_available,
        "methods": get_args(MethodType),
        'prompt_template': prompt_template
    }
