import traceback
from fastapi import APIRouter, HTTPException

from api.schemas.params import TextData
from api.models.map_reduce import do_map_reduce
from api.clients.openai import models_available

from api.schemas.response import SummaryResponse
from api.utils.logger import logger_abrege


router = APIRouter(tags=['Text'])


@router.post("/text", response_model=SummaryResponse)
async def summarize_txt(
    textData: TextData
):
    if textData.model not in models_available:
        raise HTTPException(status_code=404, detail=f"Model {textData.model} not found")
    try:
        return await do_map_reduce([textData.text], params=textData)

    except Exception as e:
        logger_abrege.error(f"{e} - trace : {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error for summary text - {e}")
