from typing import Annotated, Optional, List
from openai import OpenAI
from fastapi import HTTPException, UploadFile, APIRouter, Query
from api.models.naive import process_documents
from api.schemas.params import ParamsSummarize
from api.utils.url_parser import url_scrapper
from api.utils.pdf_handler import ModeOCR
from api.utils.parse import parse_files
from api.config.openai import OpenAISettings
from fastapi.responses import StreamingResponse
import asyncio
from typing import AsyncGenerator

client = OpenAI(
    api_key=OpenAISettings().OPENAI_API_KEY, base_url=OpenAISettings().OPENAI_API_BASE
)
models_available = [model.id for model in client.models.list().data]

context = {}

router = APIRouter(tags=['Summarize'])


@router.post("/url")
async def summarize_url(url: str, model: str, params: Optional[ParamsSummarize] = None):
    if model not in models_available:
        raise HTTPException(
            status_code=500, detail=f"{model} not Found {models_available}"
        )
    data = url_scrapper(url=url)
    docs = [doc.page_content for doc in data]

    return process_documents(docs=docs, model=model, client=client, params=params)


@router.post("/text")
async def summarize_txt(
    text: str, model: str, params: Optional[ParamsSummarize] = None
):
    return process_documents(docs=[text], model=model, client=client, params=params)


@router.post(
    "/doc",
)
async def summarize_doc(
    file: UploadFile,
    model: str,
    pdf_mode_ocr: ModeOCR | None = None,
    context_size: int = None,
    temperature: Annotated[float, Query(ge=0, le=1.0)] = 0,
    language: str = None,
    size: int = None,
    summarize_template: str | None = None,
    map_template: str | None = None,
    reduce_template: str | None = None,
    question_template: str | None = None,
    refine_template: str | None = None,
    custom_prompt: str | None = None,
):
    docs = parse_files(file=file, pdf_mode_ocr=pdf_mode_ocr)
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

    async def generate() -> AsyncGenerator[bytes, None]:
        yield "Démarrage du résumé...\n"
        await asyncio.sleep(1)  # Petit delay pour forcer l'envoi initial

        result = await asyncio.to_thread(
            process_documents, docs=docs, model=model, client=client, params=params
        )

        # Tu peux aussi rendre ça plus verbeux (ex: step by step)
        yield f"{result}\n".encode()
        yield "Résumé terminé.\n"

    return StreamingResponse(generate(), media_type="text/plain")


@router.get("/models", response_model=List[str])
async def list_model():
    """Get a list a available mode for the api"""
    return models_available
