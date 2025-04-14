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

if "OPENAI_API_MODEL" in os.environ and models_available is not None:
    if os.environ["OPENAI_API_MODEL"] not in models_available:
        logging.error(f"OPENAI_API_MODEL={os.environ['OPENAI_API_MODEL']} is not a available model. Available models are {models_available}")

router = APIRouter(tags=['Summarize'])

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
async def summarize_url(urlData : UrlData):
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
    logging.info("Récupération des modèles disponibles")
    return models_available
