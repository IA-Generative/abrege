from typing import get_args, Annotated, Optional, List, Literal
from time import perf_counter
import logging
import json
import os
import sys

from utils.url_parser import url_scrapper
from utils.pdf_handler import ModeOCR
from utils.parse import parse_files

from openai import OpenAI, APIConnectionError
from fastapi import HTTPException, UploadFile, APIRouter, Query, FastAPI, status, Form, UploadFile, File, Depends, Request
from models.naive import process_documents
from models.mapreduce import do_map_reduce
from schemas.params import MethodType, ParamsSummarize
from schemas.response import SummaryResponse
from prompt.template import prompt_template
from config.openai import OpenAISettings
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from fastapi.encoders import jsonable_encoder
from fastapi import FastAPI, File, Body, UploadFile, Request
from pydantic import BaseModel, model_validator
from fastapi.responses import HTMLResponse
from utils.url_parser import is_url_process_available, get_content_type, download_content_to_tempfile

client = OpenAI(api_key=OpenAISettings().OPENAI_API_KEY, base_url=OpenAISettings().OPENAI_API_BASE)
model_list = [ model.id for model in  client.models.list()]
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Supprimer les handlers existants (au cas où tu recharges le module, par exemple)
if logger.hasHandlers():
    logger.handlers.clear()

# Handler pour la sortie standard (console)
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(logging.DEBUG)

# Format du log
formatter = logging.Formatter(
    "[%(asctime)s] [%(levelname)s] %(name)s - %(message)s", "%Y-%m-%d %H:%M:%S"
)
stream_handler.setFormatter(formatter)

# Ajout du handler au logger
logger.addHandler(stream_handler)

try:
    models_available = [model.id for model in client.models.list().data]
except APIConnectionError as e:
    models_available = None
    logger.error(f"Unable to access models, connection problems. {repr(e)}")


if "OPENAI_API_MODEL" in os.environ and models_available is not None:
    if os.environ["OPENAI_API_MODEL"] not in models_available:
        logger.error(f"OPENAI_API_MODEL={os.environ['OPENAI_API_MODEL']} is not a available model. Available models are {models_available}")

deprecated_router = APIRouter()
router = APIRouter()

DEFAULT_SIZE = ParamsSummarize().size
DEFAULT_MODEL = ParamsSummarize().model
DEFAULT_CONTEXT_SIZE = ParamsSummarize().context_size
DEFAULT_MAP_PROMPT = ParamsSummarize().map_prompt
DEFAULT_REDUCE_PROMPT = ParamsSummarize().reduce_prompt

logger.debug(model_list)
assert DEFAULT_MODEL in model_list, f"{DEFAULT_MODEL} not found"
LIMIT_OCR_PAGES = os.environ.get('LIMIT_OCR_PAGES', 20)

class UrlData(ParamsSummarize):
    url: str


class TextData(ParamsSummarize):
    text: str


class DocData(ParamsSummarize):
    pdf_mode_ocr: ModeOCR | None = "text_and_ocr"
    
    @model_validator(mode='before')
    @classmethod
    def validate_to_json(cls, value):
        if isinstance(value, str):
            return cls(**json.loads(value))
        return value

@router.post("/url")
async def summarize_url(urlData: UrlData) -> SummaryResponse:
    url = urlData.url
    
    content_type = await get_content_type(url=url)
    logger.info(f"url: {url} is on process (content type {content_type})")
    is_direct_processable = is_url_process_available(content_type=content_type)
    is_pdf_processable = is_url_process_available(content_type=content_type, allow_content_types=['application/pdf'])
    if is_direct_processable:
        logger.debug(f"url: {url} parsable directly")
        data = url_scrapper(url=url)
        docs = [doc.page_content for doc in data]
        return await do_map_reduce(docs, params=urlData)

    if is_pdf_processable:
        logger.debug(f"url: {url}  parsable as pdf with ocr (that use summarize_doc)")
        file = await download_content_to_tempfile(url=url, suffix=".pdf", content_type="application/pdf")
        tmp_url = urlData.model_dump()
        del tmp_url['url']
        tmp_url['pdf_mode_ocr'] = "full_ocr"
        docData = DocData(**tmp_url)
        return await summarize_doc(docData=docData,file=file)
    
    return HTTPException(status_code=500, detail=f'url: {url} is not available')


@deprecated_router.get("/url", deprecated=True)
async def old_summarize_url(urlData : Annotated[UrlData, Query()]) -> SummaryResponse:
    return await summarize_url(urlData)


@router.post("/text")
async def summarize_txt(textData: TextData) -> SummaryResponse:
    text = textData.text
    
    if 0 and len(text) <= 8192:  # TODO
        prompt = PromptTemplate.from_template("""Ce qui suit est une série d'extraits d'un texte (ou le texte entier lui-même)
```
{text}
```
Rassemblez ces éléments et faites-en un résumé final et consolidé dans {language} en {size} mots au maximum. Rédigez uniquement en {language}.{custom_prompt}
""")
        llm = ChatOpenAI(
            model=textData.model, temperature=textData.temperature, api_key=OpenAISettings().OPENAI_API_KEY, base_url=OpenAISettings().OPENAI_API_BASE
        )

        llm_chain = prompt | llm | StrOutputParser()
        deb = perf_counter()
        summary = llm_chain.invoke({"text": text, "language": textData.language, "size": textData.size, "custom_prompt": textData.custom_prompt})
        elapsed = perf_counter() - deb

        return SummaryResponse(summary=summary, time=elapsed)
    else:
        # Sinon on fait le résumé le map reduce
        return await do_map_reduce([text], params=textData)


@deprecated_router.get("/text", deprecated=True)
async def old_summarize_txt(params: Annotated[TextData, Query()]) -> SummaryResponse:
    return await summarize_txt(params)

@router.post("/doc")
async def summarize_doc(docData: DocData = Body(...), file : UploadFile = File(...)) -> SummaryResponse:
    pdf_mode_ocr = docData.pdf_mode_ocr or "text_and_ocr"
    docs = parse_files(file=file, pdf_mode_ocr=pdf_mode_ocr, limit_pages_ocr=LIMIT_OCR_PAGES)

    result = await do_map_reduce(docs, params=docData)
    logger.debug(result)

    return result

@deprecated_router.post("/doc", deprecated=True)
async def old_summarize_doc(params: Annotated[DocData, Query()], file : UploadFile) -> SummaryResponse:
    return await summarize_doc(docData=params, file=file)


@router.get("/models", response_model=List[str])
async def list_model():
    """Get a list a available mode for the api"""
    return models_available


@deprecated_router.get("/default_params", deprecated=True)
@router.get("/default_params", deprecated=True)
async def param():
    """Generate a dict of default param of the app
    Return the available models, available methods and default prompt_template"""
    return {
        "models": models_available,
        "methods": get_args(MethodType),
        "prompt_template": prompt_template,
    }
