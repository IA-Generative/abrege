from typing import get_args, Annotated, Optional, List
from openai import OpenAI, APIConnectionError
from fastapi import HTTPException, UploadFile, APIRouter, Query
from models.naive import process_documents
from models.mapreduce import do_map_reduce
from schemas.params import MethodType, ParamsSummarize
from schemas.response import SummaryResponse
from prompt.template import prompt_template
from utils.url_parser import url_scrapper
from utils.pdf_handler import ModeOCR
from utils.parse import parse_files
from config.openai import OpenAISettings
import logging
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from time import perf_counter
from fastapi import FastAPI, File, Form, UploadFile
from typing import Annotated, Literal
from fastapi import FastAPI, Query
from pydantic import BaseModel, Field

client = OpenAI(api_key=OpenAISettings().OPENAI_API_KEY, base_url=OpenAISettings().OPENAI_API_BASE)

try:
    models_available = [model.id for model in client.models.list().data]
except APIConnectionError as e:
    logging.error(f"Unable to access models, connection problems. {repr(e)}")

deprecated_router = APIRouter()
router = APIRouter()

DEFAULT_SIZE = 4_000
DEFAULT_MODEL = "chat-leger"
DEFAULT_CONTEXT_SIZE = 10_000
DEFAULT_CUSTOM_PROMPT = "en français"


class UrlData(ParamsSummarize):
    url: str


class TextData(ParamsSummarize):
    text: str


class DocData(ParamsSummarize):
    file: UploadFile
    pdf_mode_ocr: ModeOCR | None = None


@router.post("/url")
async def summarize_url(urlData: UrlData) -> SummaryResponse:
    url = urlData.url
    data = url_scrapper(url=url)
    docs = [doc.page_content for doc in data]
    return await do_map_reduce(docs, params=urlData)


@deprecated_router.get("/url", deprecated=True)
async def old_summarize_url(
    url: str,
    model: str = DEFAULT_MODEL,
    context_size: int = DEFAULT_CONTEXT_SIZE,
    temperature: Annotated[float, Query(ge=0, le=1.0)] = 0,
    language: str = None,
    size: int = DEFAULT_SIZE,
    summarize_template: str | None = None,
    map_template: str | None = None,
    reduce_template: str | None = None,
    question_template: str | None = None,
    refine_template: str | None = None,
    custom_prompt: str | None = DEFAULT_CUSTOM_PROMPT,
) -> SummaryResponse:
    params: UrlData = UrlData(
        url=url,
        model=model,
        context_size=context_size,
        temperature=temperature,
        language=language,
        size=size,
        summarize_template=summarize_template,
        map_template=map_template,
        reduce_template=reduce_template,
        question_template=question_template,
        refine_template=refine_template,
        custom_prompt=custom_prompt,
    )

    return await summarize_url(params)


@router.post("/text")
async def summarize_txt(textData: TextData) -> SummaryResponse:
    text = textData.text

    if len(text) <= 8192:  # TODO
        prompt = PromptTemplate.from_template("""Ce qui suit est une série d'extraits d'un texte (ou le texte entier lui-même)
```
{text}
```
Rassemblez ces éléments et faites-en un résumé final et consolidé dans {language} en {size} mots au maximum. Rédigez uniquement en {language}.{custom_prompt}
""")
        params = textData
        llm = ChatOpenAI(
            model=params.model, temperature=params.temperature, api_key=OpenAISettings().OPENAI_API_KEY, base_url=OpenAISettings().OPENAI_API_BASE
        )

        llm_chain = prompt | llm | StrOutputParser()
        deb = perf_counter()
        summary = llm_chain.invoke({"text": text, "language": params.language, "size": params.size, "custom_prompt": params.custom_prompt})
        elapsed = perf_counter() - deb

        return SummaryResponse(summary=summary, time=elapsed)
    else:
        # Sinon on fait le résumé le map reduce
        return await do_map_reduce([text], params=params)


@deprecated_router.get("/text", deprecated=True)
async def old_summarize_txt(
    text: str,
    model: str = DEFAULT_MODEL,
    context_size: int = DEFAULT_CONTEXT_SIZE,
    temperature: Annotated[float, Query(ge=0, le=1.0)] = 0,
    language: str = None,
    size: int = DEFAULT_SIZE,
    summarize_template: str | None = None,
    map_template: str | None = None,
    reduce_template: str | None = None,
    question_template: str | None = None,
    refine_template: str | None = None,
    custom_prompt: str | None = DEFAULT_CUSTOM_PROMPT,
) -> SummaryResponse:
    params: TextData = TextData(
        text=text,
        model=model,
        context_size=context_size,
        temperature=temperature,
        language=language,
        size=size,
        summarize_template=summarize_template,
        map_template=map_template,
        reduce_template=reduce_template,
        question_template=question_template,
        refine_template=refine_template,
        custom_prompt=custom_prompt,
    )
    return await summarize_txt(params)


@router.post("/doc")
async def summarize_doc(docData: DocData) -> SummaryResponse:
    pdf_mode_ocr = docData.pdf_mode_ocr
    file = docData.file
    if pdf_mode_ocr is None:
        pdf_mode_ocr = "text_and_ocr"
    docs = parse_files(file=file, pdf_mode_ocr=pdf_mode_ocr)

    return await do_map_reduce(docs, params=docData)


@deprecated_router.post("/doc", deprecated=True)
async def old_summarize_doc(
    file: UploadFile,
    model: str = DEFAULT_MODEL,
    pdf_mode_ocr: ModeOCR | None = None,
    context_size: int = DEFAULT_CONTEXT_SIZE,
    temperature: Annotated[float, Query(ge=0, le=1.0)] = 0,
    language: str = None,
    size: int = DEFAULT_SIZE,
    summarize_template: str | None = None,
    map_template: str | None = None,
    reduce_template: str | None = None,
    question_template: str | None = None,
    refine_template: str | None = None,
    custom_prompt: str | None = DEFAULT_CUSTOM_PROMPT,
) -> SummaryResponse:
    params: DocData = DocData(
        file=file,
        pdf_mode_ocr=pdf_mode_ocr,
        model=model,
        context_size=context_size,
        temperature=temperature,
        language=language,
        size=size,
        summarize_template=summarize_template,
        map_template=map_template,
        reduce_template=reduce_template,
        question_template=question_template,
        refine_template=refine_template,
        custom_prompt=custom_prompt,
    )

    return await summarize_doc(params)


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
