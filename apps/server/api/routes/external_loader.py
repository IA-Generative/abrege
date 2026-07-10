import asyncio
import json
import os
import tempfile
import traceback
from datetime import datetime
from urllib.parse import unquote

from fastapi import APIRouter, Depends, HTTPException, Request, status

from api.core.security.token import RequestContext, parse_header_context
from src.clients import celery_app, file_connector
from src.schemas.content import DocumentModel
from src.schemas.parameters import SummaryParameters
from src.schemas.task import TaskForm, TaskModel, TaskStatus, TaskUpdateForm, task_table
from src.utils.logger import logger_abrege as logger

router = APIRouter(tags=["External Document Loader"])

EXTERNAL_DOCUMENT_LOADER_API_KEY = os.environ.get("EXTERNAL_DOCUMENT_LOADER_API_KEY")
POLL_INTERVAL_SECONDS = float(os.environ.get("EXTERNAL_LOADER_POLL_INTERVAL_SECONDS", 2))
MAX_WAIT_SECONDS = float(os.environ.get("EXTERNAL_LOADER_MAX_WAIT_SECONDS", 600))

if not EXTERNAL_DOCUMENT_LOADER_API_KEY:
    logger.warning("EXTERNAL_DOCUMENT_LOADER_API_KEY is not set: /process is unauthenticated")


def verify_external_loader_request(request: Request) -> RequestContext:
    ctx = parse_header_context(request, is_fastapi=True)
    if EXTERNAL_DOCUMENT_LOADER_API_KEY and ctx.token != EXTERNAL_DOCUMENT_LOADER_API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="UNAUTHORIZED")
    if not ctx.user_id:
        ctx.user_id = "openwebui"
    return ctx


def _build_documents(task: TaskModel) -> list[dict]:
    """Compatible with OpenWebUI's ExternalDocumentLoader: a list of {page_content, metadata}."""
    output = task.output
    documents: list[dict] = []
    if output is None:
        return documents

    summary = getattr(output, "summary", None)
    if summary:
        documents.append(
            {
                "page_content": summary,
                "metadata": {
                    "type": "summary",
                    "task_id": task.id,
                    "word_count": getattr(output, "word_count", None),
                },
            }
        )

    for qa in getattr(output, "qa_items", None) or []:
        documents.append(
            {
                "page_content": f"Q: {qa.question}\nA: {qa.answer}",
                "metadata": {
                    "type": "qa",
                    "task_id": task.id,
                    "page": qa.page,
                    "question": qa.question,
                    "answer": qa.answer,
                },
            }
        )

    for i, page_text in enumerate(output.texts_found or []):
        if not page_text:
            continue
        documents.append(
            {
                "page_content": page_text,
                "metadata": {
                    "type": "ocr_page",
                    "task_id": task.id,
                    "page": i + 1,
                },
            }
        )

    return documents


def _cleanup_task(user_id: str, task_id: str) -> None:
    """Remove the uploaded file and the task record — nothing is kept after /process responds."""
    try:
        file_connector.delete_by_task_id(user_id, task_id)
    except Exception as e:
        logger.warning(f"External loader: failed to delete file for task {task_id}: {e}")
    try:
        task_table.delete_task_by_id(task_id)
    except Exception as e:
        logger.warning(f"External loader: failed to delete task {task_id}: {e}")


@router.put("/process")
async def process_document(
    request: Request,
    ctx: RequestContext = Depends(verify_external_loader_request),
):
    user_id: str = ctx.user_id or "openwebui"

    body = await request.body()
    if not body:
        raise HTTPException(status_code=422, detail="Empty request body")

    content_type = request.headers.get("content-type") or "application/octet-stream"
    raw_filename = unquote(request.headers.get("x-filename", "document"))
    _, extension = os.path.splitext(raw_filename)

    task_data = task_table.insert_new_task(
        user_id=user_id,
        form_data=TaskForm(
            type="summary",
            status=TaskStatus.CREATED.value,
            parameters=SummaryParameters(extract_qa=True),
            extras={"source": "openwebui-external-loader"},
        ),
    )
    if task_data is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to create task")
    task_id: str = task_data.id

    try:
        temp_file_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as temp_file:
                temp_file_path = temp_file.name
                temp_file.write(body)

            saved_path = file_connector.save(user_id, task_id, temp_file_path)

            document_content = DocumentModel(
                created_at=int(datetime.now().timestamp()),
                file_path=saved_path,
                raw_filename=raw_filename,
                content_type=content_type,
                ext=extension,
                size=len(body),
                extras={},
            )

            updated_task = task_table.update_task(
                task_id=task_id,
                form_data=TaskUpdateForm(status=TaskStatus.QUEUED.value, input=document_content),
            )
            if updated_task is None:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to queue task")

            celery_app.send_task(
                "worker.tasks.abrege",
                args=[json.dumps(updated_task.model_dump())],
                task_id=task_id,
                retries=2,
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"External loader: failed to submit task {task_id}: {e} - {traceback.format_exc()}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Document processing failed")
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)

        waited = 0.0
        while waited < MAX_WAIT_SECONDS:
            current = task_table.get_task_by_id(task_id)
            if current is None:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Task not found")

            if current.status == TaskStatus.COMPLETED.value:
                return _build_documents(current)

            if current.status == TaskStatus.FAILED.value:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Document processing failed")

            await asyncio.sleep(POLL_INTERVAL_SECONDS)
            waited += POLL_INTERVAL_SECONDS

        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="Document processing timed out")
    finally:
        _cleanup_task(user_id, task_id)
