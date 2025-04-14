import traceback
from fastapi import HTTPException, APIRouter
from api.schemas.params import UrlData
from api.utils.url_parser import url_scrapper
from api.models.map_reduce import do_map_reduce
from api.clients.openai import models_available
from api.utils.logger import logger_abrege
from api.schemas.response import SummaryResponse

router = APIRouter(tags=['Url'])


@router.post("/url", response_model=SummaryResponse)
async def summarize_url(urlData: UrlData):
    if urlData.model not in models_available:
        raise HTTPException(
            status_code=404, detail=f"{urlData.model} not Found {models_available}"
        )

    try:

        data = url_scrapper(url=urlData.url)
        docs = [doc.page_content for doc in data]

        return await do_map_reduce(docs, params=urlData)

    except Exception as e:
        logger_abrege.error(f"{e} - trace : {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error for summary text - {e}")
