from typing import List
from api.schemas.params import TextData, DocData
from api.utils.parse import parse_files
from api.models.map_reduce import do_map_reduce
from api.clients.openai import models_available
from fastapi import File, Body, UploadFile, APIRouter
from api.schemas.response import SummaryResponse


context = {}

router = APIRouter(tags=['Text'])

DEFAULT_SIZE = 4_000
DEFAULT_MODEL = "chat-leger"
DEFAULT_CONTEXT_SIZE = 10_000
DEFAULT_CUSTOM_PROMPT = "en français"


@router.post("/text")
async def summarize_txt(
    textData: TextData
):
    return await do_map_reduce([textData.text], params=textData)
