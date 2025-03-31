from typing import Annotated, Optional, List
from openai import OpenAI
from fastapi import HTTPException, UploadFile, APIRouter, Query, Body, File
from api.models.naive import process_documents
from api.schemas.params import ParamsSummarize, UrlData, TextData, DocData
from api.utils.url_parser import url_scrapper
from api.utils.pdf_handler import ModeOCR
from api.utils.parse import parse_files
from api.config.openai import OpenAISettings
from api.models.map_reduce import do_map_reduce

client = OpenAI(
    api_key=OpenAISettings().OPENAI_API_KEY, base_url=OpenAISettings().OPENAI_API_BASE
)
models_available = [model.id for model in client.models.list().data]

context = {}

router = APIRouter(tags=['Summarize'])

DEFAULT_SIZE = 4_000
DEFAULT_MODEL = "chat-leger"
DEFAULT_CONTEXT_SIZE = 10_000
DEFAULT_CUSTOM_PROMPT = "en français"


@router.post("/url")
async def summarize_url(urlData: UrlData):
    if urlData.model not in models_available:
        raise HTTPException(
            status_code=500, detail=f"{urlData.model} not Found {models_available}"
        )
    data = url_scrapper(url=urlData.url)
    docs = [doc.page_content for doc in data]

    return await do_map_reduce(docs, params=urlData)


@router.post("/text")
async def summarize_txt(
    textData: TextData
):
    return await do_map_reduce([textData.text], params=textData)


@router.post(
    "/doc",
)
async def summarize_doc(
    docData: DocData = Body(...),
    file: UploadFile = File(...),

):
    docs = parse_files(file=file, pdf_mode_ocr=docData.pdf_mode_ocr)

    return await do_map_reduce(docs, params=docData)


@router.get("/models", response_model=List[str])
async def list_model():
    """Get a list a available mode for the api"""
    return models_available
