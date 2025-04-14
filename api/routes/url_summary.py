from openai import OpenAI
from fastapi import HTTPException, APIRouter
from api.models.naive import process_documents
from api.schemas.params import ParamsSummarize, UrlData
from api.utils.url_parser import url_scrapper
from api.config.openai import OpenAISettings
from api.models.map_reduce import do_map_reduce
from api.clients.openai import models_available

router = APIRouter(tags=['Url'])


@router.post("/url")
async def summarize_url(urlData: UrlData):
    if urlData.model not in models_available:
        raise HTTPException(
            status_code=500, detail=f"{urlData.model} not Found {models_available}"
        )
    data = url_scrapper(url=urlData.url)
    docs = [doc.page_content for doc in data]

    return await do_map_reduce(docs, params=urlData)
