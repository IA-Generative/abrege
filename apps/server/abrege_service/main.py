import os

# Must run before `transformers` is imported anywhere in the process (directly or via
# abrege_service.utils.text/tokenizer): its own logging setup reads this env var once, at
# import time, and otherwise prints plain-text advisories (e.g. "PyTorch was not found")
# straight to stderr, breaking JSON log pipelines.
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")

from typing import List
import time
import json
import asyncio
import traceback

import openai
from langchain_openai import ChatOpenAI
from abrege_service.utils.file import hash_file, hash_string
from abrege_service.modules.base import BaseService
from abrege_service.modules.url import URLService
from abrege_service.modules.doc import (
    HtmlToMdService,
    FlatTextService,
    MicrosoftOlderDocumentToMdService,
)
from abrege_service.modules.image import ImageFromVLM
from abrege_service.modules.ocr import OCRMIService
from abrege_service.modules.cache import CacheService

from abrege_service.models.summary.parallele_summary_chain import (
    LangChainAsyncMapReduceService,
)
from abrege_service.models.summary.qa_chain import build_qa_runnable
from abrege_service.models.summary.entity_chain import (
    build_entity_runnable,
    build_global_relationship_runnable,
)
from abrege_service.models.summary.topic_chain import build_topic_runnable
from abrege_service.models.summary.chunk_chain import build_chunk_runnable
from abrege_service.config.openai import OpenAISettings

from src.schemas.task import TaskModel, task_table, TaskStatus, TaskUpdateForm
from src.schemas.content import URLModel, DocumentModel, TextModel
from src.schemas.result import ResultModel
from src.schemas.parameters import SummaryParameters
from src.schemas.entity import entity_table
from src.clients import celery_app, file_connector, redis_client
from src.clients.internal_api import internal_api_client
from src import __version__
from src.utils.logger import logger_abrege

import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration

from src.config.sentry import SentrySettings

_sentry_settings = SentrySettings()
if _sentry_settings.SENTRY_WORKER_DSN:
    try:
        sentry_sdk.init(
            dsn=_sentry_settings.SENTRY_WORKER_DSN,
            send_default_pii=_sentry_settings.SEND_DEFAULT_PII,
            environment=os.getenv("ENVIRONMENT", "development"),
            integrations=[CeleryIntegration()],
        )
    except Exception as e:
        logger_abrege.warning(f"Sentry initialization failed, continuing without it: {e}")

openai_settings = OpenAISettings()
cache_service = CacheService()
html_service = HtmlToMdService()
microsoft_service_older = MicrosoftOlderDocumentToMdService()
flat_text_service = FlatTextService()

async_client = openai.AsyncOpenAI(
    api_key=openai_settings.OPENAI_API_KEY,
    base_url=openai_settings.OPENAI_API_BASE_URL,
)
if os.environ.get("OCR_SERVICE_LLM") == "LLM":
    ocr_service = ImageFromVLM(client=async_client, model_name=openai_settings.OPENAI_VLM_MODEL_NAME)
else:
    ocr_service = OCRMIService(url_ocr=os.environ.get("OCR_BACKEND_URL"))
services: List[BaseService] = [
    cache_service,
    microsoft_service_older,
    html_service,
    flat_text_service,
    ocr_service,
]
url_service = URLService(services=services)


client = openai.OpenAI(
    api_key=openai_settings.OPENAI_API_KEY,
    base_url=openai_settings.OPENAI_API_BASE_URL,
)


llm = ChatOpenAI(
    model=openai_settings.OPENAI_API_MODEL,
    temperature=0.0,
    api_key=openai_settings.OPENAI_API_KEY,
    base_url=openai_settings.OPENAI_API_BASE_URL,
)
summary_service = LangChainAsyncMapReduceService(
    llm=llm,
    max_token=int(os.getenv("MAX_MODEL_TOKEN", 128_000)),
    max_concurrency=int(os.getenv("MAX_CONCURRENCY_LLM_CALL", 5)),
)
def _llm_for(model_name: str | None) -> ChatOpenAI:
    """The side extractions (Q&A, entities, chunking, topics) can each be pinned to their
    own model via env vars; unset (the default) reuses the summary's own `llm` instance."""
    if not model_name or model_name == llm.model_name:
        return llm
    return ChatOpenAI(
        model=model_name,
        temperature=0.0,
        api_key=openai_settings.OPENAI_API_KEY,
        base_url=openai_settings.OPENAI_API_BASE_URL,
    )


qa_llm = _llm_for(openai_settings.QA_MODEL_NAME)
entity_llm = _llm_for(openai_settings.ENTITY_MODEL_NAME)
chunk_llm = _llm_for(openai_settings.CHUNK_MODEL_NAME)
topic_llm = _llm_for(openai_settings.TOPIC_MODEL_NAME)

qa_runnable = build_qa_runnable(qa_llm)
entity_runnable = build_entity_runnable(entity_llm)
# Global relationships are inferred from entities already extracted, so they follow the
# same model as entity extraction rather than getting their own setting.
global_relationship_runnable = build_global_relationship_runnable(entity_llm)
topic_runnable = build_topic_runnable(topic_llm)
chunk_runnable = build_chunk_runnable(chunk_llm)
tmp_folder = os.environ.get("CACHE_FOLDER")
os.makedirs(tmp_folder, exist_ok=True)


@celery_app.task(name="worker.tasks.abrege", bind=True)
def launch(self, task: str):
    task: TaskModel = TaskModel.model_validate(json.loads(task))
    task.extras = task.extras or {}
    sentry_sdk.set_tag("task.id", task.id)
    sentry_sdk.set_user({"id": task.user_id})
    extra_log = {"user_id": task.user_id, "task_id": task.id, "action": "launch"}
    try:
        task_table.update_task(
            task_id=task.id,
            form_data=TaskUpdateForm(
                status=TaskStatus.IN_PROGRESS.value,
                updated_at=int(time.time()),
            ),
        )
        t = time.time()
        if isinstance(task.input, URLModel):
            logger_abrege.debug(f"Processing URL task: {task.id}", extra=extra_log)
            task = url_service.process_task(task=task)

        elif isinstance(task.input, DocumentModel):
            logger_abrege.debug(f"Processing Document task: {task.id}", extra=extra_log)
            file_path = file_connector.get_by_task_id(user_id=task.user_id, task_id=task.id)
            task.input.file_path = file_path
            task.content_hash = hash_file(file_path)
            for service in services:
                if service.is_available(task):
                    logger_abrege.debug(f"Using service: {service.__class__.__name__}", extra=extra_log)
                    task = service.process_task(task=task)
                    break

            if os.path.exists(file_path):
                os.remove(file_path)

        elif isinstance(task.input, TextModel):
            logger_abrege.debug(f"Processing Text task: {task.id}", extra=extra_log)
            task.content_hash = hash_string(task.input.text)
            task.output = ResultModel(
                type="flat",
                created_at=task.input.created_at,
                model_name="flat",
                model_version=__version__,
                percentage=1,
                texts_found=[task.input.text],
            )

        else:
            raise NotImplementedError("Content type not supported")

        logger_abrege.debug(f"Task processed in {time.time() - t} seconds", extra=extra_log)

        t = time.time()
        task = summary_service.process_task(task=task)
        logger_abrege.info(
            f"Summary Task {task.id} processed in {time.time() - t} seconds",
            extra=extra_log,
        )
        return task.model_dump()

    except Exception as e:
        task_table.update_task(
            task_id=task.id,
            form_data=TaskUpdateForm(
                status=TaskStatus.FAILED.value,
                updated_at=int(time.time()),
                extras={"error": f"{e} - {traceback.format_exc()}"},
            ),
        )
        logger_abrege.error(f"Task {task.id} failed: {e} - {traceback.format_exc()}")
        raise e


@celery_app.task(name="worker.tasks.extract_chunk_details", bind=True)
def extract_chunk_details(self, payload: str):
    """Extract Q&A, entities/local relationships and semantic sub-chunks for a single map-step
    window, and persist them all.

    Runs as its own Celery message, fully decoupled from the parent summarize task, so it
    never adds latency to `worker.tasks.abrege`. The last chunk of a task to finish triggers
    the follow-up global-relationships pass (see `dispatch_all_chunks`).
    """
    data = json.loads(payload)
    task_id = data["task_id"]
    chunk_index = data["chunk_index"]
    page = data["page"]
    extra_log = {"task_id": task_id, "chunk_index": chunk_index}
    try:

        async def run():
            return await asyncio.gather(
                qa_runnable.ainvoke({"text": data["text"], "language": data["language"], "qa_per_chunk": data["qa_per_chunk"]}),
                entity_runnable.ainvoke({"text": data["text"], "language": data["language"]}),
                chunk_runnable.ainvoke({"text": data["text"]}),
            )

        qa_output, entity_output, chunk_output = asyncio.run(run())

        internal_api_client.save_chunk_qa_items(
            task_id=task_id,
            chunk_index=chunk_index,
            qa_items=[
                {"page": page, "source_text": data["text"], "question": item.question, "answer": item.answer}
                for item in qa_output.items
            ],
            model_name=qa_llm.model_name,
        )
        internal_api_client.save_chunk_entities(
            task_id=task_id,
            chunk_index=chunk_index,
            entities=[
                {"type": e.type, "text": e.text, "contexts": e.contexts, "pages": [page] if page is not None else []}
                for e in entity_output.entities
            ],
            relationships=[r.model_dump() for r in entity_output.relationships],
            model_name=entity_llm.model_name,
        )
        internal_api_client.save_chunks(
            task_id=task_id,
            chunk_index=chunk_index,
            page=page,
            chunks=chunk_output.chunks or [data["text"]],
            model_name=chunk_llm.model_name,
        )
    except Exception as e:
        logger_abrege.error(f"Chunk details extraction failed: {e} - {traceback.format_exc()}", extra=extra_log)
        task_table.update_task(task_id=task_id, form_data=TaskUpdateForm(qa_entities_status="failed"))
        raise e

    remaining = redis_client.decr(f"chunk_pending:{task_id}")
    if remaining <= 0:
        redis_client.delete(f"chunk_pending:{task_id}")
        task_table.update_task(
            task_id=task_id, form_data=TaskUpdateForm(qa_entities_status="completed", relationships_status="pending")
        )
        celery_app.send_task(
            "worker.tasks.compute_global_relationships",
            args=[json.dumps({"task_id": task_id})],
            task_id=f"{task_id}:global-relationships",
        )


@celery_app.task(name="worker.tasks.compute_global_relationships", bind=True)
def compute_global_relationships(self, payload: str):
    """Infer relationships across every entity already extracted for a task, once all its
    chunks are done, so entities found in different chunks can still be linked together."""
    data = json.loads(payload)
    task_id = data["task_id"]
    try:
        entity_rows = entity_table.get_entities_by_task(task_id)
        if len(entity_rows) < 2:
            task_table.update_task(task_id=task_id, form_data=TaskUpdateForm(relationships_status="completed"))
            return
        entities_list = "\n".join(f"{i}: {e.type} - {e.text} - pages {e.pages}" for i, e in enumerate(entity_rows))
        output = asyncio.run(global_relationship_runnable.ainvoke({"entities_list": entities_list}))
        internal_api_client.save_global_relationships(
            task_id=task_id,
            entity_ids_in_order=[e.id for e in entity_rows],
            relationships=[r.model_dump() for r in output.relationships],
            model_name=entity_llm.model_name,
        )
        task_table.update_task(task_id=task_id, form_data=TaskUpdateForm(relationships_status="completed"))
    except Exception as e:
        logger_abrege.error(f"Global relationships computation failed: {e} - {traceback.format_exc()}", extra={"task_id": task_id})
        task_table.update_task(task_id=task_id, form_data=TaskUpdateForm(relationships_status="failed"))
        raise e


@celery_app.task(name="worker.tasks.extract_task_details", bind=True)
def extract_task_details(self, task_id: str):
    """Re-run Q&A/entities/relationships extraction for a task that was summarized without
    it (`extract_qa=False` at the time), on user demand, without re-running the summary."""
    task = task_table.get_task_by_id(task_id)
    if task is None or task.output is None or not task.output.texts_found:
        logger_abrege.warning(f"Task {task_id} has no source text, cannot extract details.", extra={"task_id": task_id})
        return

    params = task.parameters or SummaryParameters()
    qa_per_chunk = params.qa_per_chunk if params.qa_per_chunk else 3
    language = params.language or "French"

    texts = summary_service.split_task_texts(task)
    task_table.update_task(task_id=task.id, form_data=TaskUpdateForm(qa_entities_status="in_progress"))
    summary_service.dispatch_all_chunks(task_id=task.id, texts=texts, language=language, qa_per_chunk=qa_per_chunk)


@celery_app.task(name="worker.tasks.classify_topics", bind=True)
def classify_topics(self, payload: str):
    """Free-form topic/subject classification of a task's final summary, with a confidence
    score and an explanation per topic. Fired once the summary is complete, fully decoupled
    from `worker.tasks.abrege` — it never adds latency to the summary itself."""
    data = json.loads(payload)
    task_id = data["task_id"]
    try:
        output = asyncio.run(topic_runnable.ainvoke({"text": data["summary"], "language": data["language"]}))
        internal_api_client.save_topics(
            task_id=task_id,
            topics=[{"topic": t.topic, "confidence": t.confidence, "explanation": t.explanation} for t in output.topics],
            model_name=topic_llm.model_name,
        )
        task_table.update_task(task_id=task_id, form_data=TaskUpdateForm(topics_status="completed"))
    except Exception as e:
        logger_abrege.error(f"Topic classification failed: {e} - {traceback.format_exc()}", extra={"task_id": task_id})
        task_table.update_task(task_id=task_id, form_data=TaskUpdateForm(topics_status="failed"))
        raise e
