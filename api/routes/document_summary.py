from api.schemas.params import DocData
from api.utils.parse import parse_files
from api.models.map_reduce import do_map_reduce
from fastapi import File, Body, UploadFile, APIRouter
from api.schemas.response import SummaryResponse


router = APIRouter(tags=['Documents'])


@router.post(
    "/doc", response_model=SummaryResponse
)
async def summarize_doc(
    docData: DocData = Body(...),
    file: UploadFile = File(...),

):
    docs = parse_files(file=file, pdf_mode_ocr=docData.pdf_mode_ocr)

    return await do_map_reduce(docs, params=docData)
