from typing import get_args, Annotated, Optional, List
from openai import OpenAI, APIConnectionError
from fastapi import HTTPException, UploadFile, APIRouter, Query
from models.naive import process_documents
from models.mapreduce import do_map_reduce
from schemas.params import MethodType, ParamsSummarize
from prompt.template import prompt_template
from utils.url_parser import url_scrapper
from utils.pdf_handler import ModeOCR
from utils.parse import parse_files
from config.openai import OpenAISettings
import logging
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

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


DEFAULT_PARAM = ParamsSummarize()

@router.post("/url")
async def summarize_url(url: str, params: ParamsSummarize = DEFAULT_PARAM):
    data = url_scrapper(url=url)
    docs = [doc.page_content for doc in data]
    #try:
    return await do_map_reduce(docs, params=params)
    #except Exception as e:
    #    raise HTTPException(status_code=500, detail=str(e))


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
):
    params: ParamsSummarize = ParamsSummarize(
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

    return await summarize_url(url=url, params=params)


@router.post("/text")
async def summarize_txt(text: str, params: ParamsSummarize = DEFAULT_PARAM):
    if len(text) <= 8192:  # TODO
        prompt = PromptTemplate.from_template("""Ce qui suit est une série d'extraits d'un texte (ou le texte entier lui-même)
```
{text}
```
Take these and distill it into a consolidated summary in {language} in at most {size} words.{custom_prompt}
""")
        llm = ChatOpenAI(model=params.model, temperature=params.temperature, api_key=OpenAISettings().OPENAI_API_KEY, base_url=OpenAISettings().OPENAI_API_BASE)

        llm_chain = prompt | llm | StrOutputParser()
        import logging
        logging.warning(f"{params=}")
        return llm_chain.invoke({"text": text, "language": params.language, "size": params.size, "custom_prompt": params.custom_prompt})

    # Sinon on fait le résumé le map reduce
    summary = await do_map_reduce([text], params=params)
    return {"summary": summary}


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
):
    params: ParamsSummarize = ParamsSummarize(
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
    return await summarize_txt(text=text, params=params)


@router.post("/doc")
async def summarize_doc(file: UploadFile, pdf_mode_ocr: ModeOCR = "text_and_ocr", params: ParamsSummarize = DEFAULT_PARAM):
    docs = parse_files(file=file, pdf_mode_ocr=pdf_mode_ocr)

    return await do_map_reduce(docs, params=params)


@deprecated_router.post("/doc", deprecated=True)
async def old_summarize_doc(
    file: UploadFile,
    model: str = DEFAULT_MODEL,
    pdf_mode_ocr: ModeOCR = "text_and_ocr",
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
):
    params: ParamsSummarize = ParamsSummarize(
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

    return await summarize_doc(file, pdf_mode_ocr, params)


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
