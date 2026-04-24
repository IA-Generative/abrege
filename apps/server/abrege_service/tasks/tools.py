import os
from typing import List

import openai
from langchain_openai import ChatOpenAI
from abrege_service.modules.base import BaseService
from abrege_service.modules.url import URLService
from abrege_service.modules.audio import AudioVoskTranscriptionService
from abrege_service.modules.video import VideoTranscriptionService
from abrege_service.modules.documents.openoffice import LibreOfficeDocumentToMdService
from abrege_service.modules.doc import (
    MicrosoftDocumnentToMdService,
    FlatTextService,
    MicrosoftOlderDocumentToMdService,
    # PDFTOMD4LLMService,
)
from abrege_service.modules.image import ImageFromVLM
from abrege_service.modules.ocr import OCRMIService
from abrege_service.modules.cache import CacheService

from abrege_service.models.summary.parallele_summary_chain import (
    LangChainAsyncMapReduceService,
)
from abrege_service.config.openai import OpenAISettings

from abrege_service.clients.server import ServerClient

openai_settings = OpenAISettings()
server_client = ServerClient()
cache_service = CacheService()
audio_service = AudioVoskTranscriptionService(service_ratio_representaion=0.5)
video_service = VideoTranscriptionService(service_ratio_representaion=0.5)
microsof_service = MicrosoftDocumnentToMdService()
microsoft_service_older = MicrosoftOlderDocumentToMdService()
libre_office_service = LibreOfficeDocumentToMdService()
flat_text_service = FlatTextService()

if os.environ.get("OCR_SERVICE_LLM") == "LLM":
    ocr_service = ImageFromVLM()
else:
    ocr_service = OCRMIService(url_ocr=os.environ.get("OCR_BACKEND_URL"))
services: List[BaseService] = [
    cache_service,
    audio_service,
    video_service,
    microsoft_service_older,
    microsof_service,
    flat_text_service,
    ocr_service,
    libre_office_service,
]
url_service = URLService(services=services)


client = openai.OpenAI(
    api_key=openai_settings.OPENAI_API_KEY,
    base_url=openai_settings.OPENAI_API_BASE,
)


llm = ChatOpenAI(
    model=openai_settings.OPENAI_API_MODEL,
    temperature=0.0,
    api_key=openai_settings.OPENAI_API_KEY,
    base_url=openai_settings.OPENAI_API_BASE,
)
summary_service = LangChainAsyncMapReduceService(
    llm=llm,
    max_token=int(os.getenv("MAX_MODEL_TOKEN", 128_000)),
    max_concurrency=int(os.getenv("MAX_CONCURRENCY_LLM_CALL", 5)),
)
tmp_folder = os.environ.get("CACHE_FOLDER")
os.makedirs(tmp_folder, exist_ok=True)
