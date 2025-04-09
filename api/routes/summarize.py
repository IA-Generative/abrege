from typing import get_args, Annotated, Optional, List, Literal
from time import perf_counter
import logging
import json
import os

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

client = OpenAI(api_key=OpenAISettings().OPENAI_API_KEY, base_url=OpenAISettings().OPENAI_API_BASE)

try:
    models_available = [model.id for model in client.models.list().data]
except APIConnectionError as e:
    models_available = None
    logging.error(f"Unable to access models, connection problems. {repr(e)}")


if "OPENAI_API_MODEL" in os.environ and models_available is not None:
    if os.environ["OPENAI_API_MODEL"] not in models_available:
        logging.error(f"OPENAI_API_MODEL={os.environ['OPENAI_API_MODEL']} is not a available model. Available models are {models_available}")

deprecated_router = APIRouter()
router = APIRouter()

DEFAULT_SIZE = ParamsSummarize().size
DEFAULT_MODEL = ParamsSummarize().model
DEFAULT_CONTEXT_SIZE = ParamsSummarize().context_size
DEFAULT_MAP_PROMPT = ParamsSummarize().map_prompt
DEFAULT_REDUCE_PROMPT = ParamsSummarize().reduce_prompt

LIMIT_OCR_PAGES = 2

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
    logging.info(f"Début du résumé d'URL: {urlData.url}")
    start_time = perf_counter()
    
    url = urlData.url
    data = url_scrapper(url=url)
    docs = [doc.page_content for doc in data]
    
    logging.info(f"URL scrappée avec succès, {len(docs)} documents extraits")
    result = await do_map_reduce(docs, params=urlData)
    
    elapsed_time = perf_counter() - start_time
    logging.info(f"Résumé d'URL terminé en {elapsed_time:.2f} secondes")
    return result


@deprecated_router.get("/url", deprecated=True)
async def old_summarize_url(urlData : Annotated[UrlData, Query()]) -> SummaryResponse:
    return await summarize_url(urlData)


@router.post("/text")
async def summarize_txt(textData: TextData) -> SummaryResponse:
    logging.info(f"Début du résumé de texte, taille: {len(textData.text)} caractères")
    start_time = perf_counter()
    
    text = textData.text
    
    if 0 and len(text) <= 8192:  # TODO
        logging.info("Utilisation de la méthode directe pour le résumé")
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

        logging.info(f"Résumé de texte terminé en {elapsed:.2f} secondes")
        return SummaryResponse(summary=summary, time=elapsed)
    else:
        logging.info("Utilisation de la méthode map-reduce pour le résumé")
        result = await do_map_reduce([text], params=textData)
        elapsed_time = perf_counter() - start_time
        logging.info(f"Résumé de texte terminé en {elapsed_time:.2f} secondes")
        return result


@deprecated_router.get("/text", deprecated=True)
async def old_summarize_txt(params: Annotated[TextData, Query()]) -> SummaryResponse:
    return await summarize_txt(params)

@router.post("/doc")
async def summarize_doc(docData: DocData = Body(...), file : UploadFile = File(...)) -> SummaryResponse:
    logging.info(f"Début du résumé de document: {file.filename}")
    start_time = perf_counter()
    
    pdf_mode_ocr = docData.pdf_mode_ocr or "text_and_ocr"
    logging.info(f"Mode OCR sélectionné: {pdf_mode_ocr}")
    
    docs = parse_files(file=file, pdf_mode_ocr=pdf_mode_ocr, limit_pages_ocr=LIMIT_OCR_PAGES)
    logging.info(f"Document parsé avec succès, {len(docs)} pages traitées")

    result = await do_map_reduce(docs, params=docData)
    elapsed_time = perf_counter() - start_time
    logging.info(f"Résumé de document terminé en {elapsed_time:.2f} secondes")
    return result

@deprecated_router.post("/doc", deprecated=True)
async def old_summarize_doc(params: Annotated[DocData, Query()], file : UploadFile) -> SummaryResponse:
    return await summarize_doc(docData=params, file=file)


@router.get("/models", response_model=List[str])
async def list_model():
    """Get a list a available mode for the api"""
    logging.info("Récupération des modèles disponibles")
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
