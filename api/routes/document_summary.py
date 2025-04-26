from fastapi import File, Body, UploadFile, APIRouter, HTTPException
import traceback

from api.schemas.params import DocData
from api.utils.parse import parse_files
from api.models.map_reduce import do_map_reduce
from api.schemas.response import SummaryResponse
from api.utils.logger import logger_abrege
from api.clients.openai import models_available


router = APIRouter(tags=["Documents"])


@router.post("/doc", response_model=SummaryResponse)
async def summarize_doc(
    docData: DocData = Body(...),
    file: UploadFile = File(...),
):
    if docData.model not in models_available:
        raise HTTPException(status_code=404, detail=f"Model {docData.model} not found")
    try:
        docs = parse_files(file=file, pdf_mode_ocr=docData.pdf_mode_ocr)

        return await do_map_reduce(docs, params=docData)
    except Exception as e:
        logger_abrege.error(f"{e} - trace : {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error for summary text - {e}")
