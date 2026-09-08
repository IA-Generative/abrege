import os
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel


from api.core.security.token import RequestContext
from api.core.security.factory import TokenVerifier
from api.core.security.internal import verify_internal_service

from src.schemas.task import task_table, TaskModel, TaskUpdateForm, TaskStatus
from src.schemas.pagination import Pagination
from src.schemas.code_error import TASK_STATUS_TO_HTTP
from src.schemas.qa_item import qa_item_table, QAItemRowModel
from src.schemas.entity import entity_table, EntityRowModel, RelationshipRowModel
from src.schemas.result import EntityModel, QAItem, RelationshipModel
from src.clients import file_connector, celery_app
from src.clients.ocr_client import OCRClient
from src.utils.logger import logger_abrege

# Optional: only used to propagate task cancellation to the OCR service (below). Building
# it can now raise (see src.clients.ocr_client.build_token_manager, abrege#354) when OCR
# delegation has no usable auth configured, or when OCR_BACKEND_URL isn't set - that must
# not block the whole API from booting over what only the cancellation path needs.
try:
    ocr_backend_url = os.getenv("OCR_BACKEND_URL")
    if not ocr_backend_url:
        raise RuntimeError("OCR_BACKEND_URL is not set")
    ocr_client = OCRClient(url=ocr_backend_url)
except RuntimeError as e:
    logger_abrege.warning(f"OCR client not configured, task cancellation will not propagate to it: {e}")
    ocr_client = None

router = APIRouter(tags=["Tasks"])


@router.get("/task/{id}", response_model=TaskModel)
async def get_task(
    id: str,
    show_text_found: bool = False,
    ctx: RequestContext = Depends(TokenVerifier),
) -> TaskModel:
    task = task_table.get_task_by_id(task_id=id)
    if task is None or task.user_id != ctx.user_id:
        raise HTTPException(404, detail=f"{id} not found")
    logger_abrege.debug(
        f"[task id : {task.id}][user id: {task.user_id}]",
        extra={"task_id": task.id, "user_id": task.user_id},
    )
    task.position = task_table.get_position_in_queue(task_id=id)
    if not show_text_found and task.output is not None:
        task.output = task.output.model_copy()
        task.output.texts_found = []

    return JSONResponse(task.model_dump(), status_code=TASK_STATUS_TO_HTTP.get(task.status, 200))


def read_user(user_id: str, offset: int = 1, limit: int = 10) -> List[TaskModel]:
    tmp_log = {"user_id": user_id}
    try:
        tasks = task_table.get_tasks_by_user_id(user_id=user_id, page=offset, page_size=limit)
        logger_abrege.debug(f"[Task found: {len(tasks)}]", extra=tmp_log)
        if tasks is None:
            raise HTTPException(404, detail=f"{id} not found")
    except Exception as e:
        logger_abrege.error(e, extra=tmp_log)
        raise HTTPException(500, detail=f"{str(e)} not found")

    return tasks


@router.get("/task/user/", response_model=Pagination[TaskModel])
async def get_tasks_read_user(
    offset: int = 1,
    limit: int = 10,
    ctx: RequestContext = Depends(TokenVerifier),
) -> Pagination[TaskModel]:
    tasks = read_user(user_id=ctx.user_id, offset=offset, limit=limit)
    total = task_table.count_tasks_by_user_id(user_id=ctx.user_id)
    return Pagination[TaskModel](total=total, page=offset, page_size=limit, items=tasks)


@router.post("/task/{id}/cancel", response_model=TaskModel)
async def cancel_task(
    id: str,
    ctx: RequestContext = Depends(TokenVerifier),
):
    task = task_table.get_task_by_id(task_id=id)
    if task is None or task.user_id != ctx.user_id:
        raise HTTPException(404, detail=f"{id} not found")
    if task.status not in [
        TaskStatus.CREATED,
        TaskStatus.QUEUED,
        TaskStatus.STARTED,
        TaskStatus.IN_PROGRESS,
    ]:
        raise HTTPException(400, detail=f"{id} cannot be canceled (status: {task.status})")

    celery_app.control.revoke(id, terminate=True)

    updated = task_table.update_task(
        task_id=id,
        form_data=TaskUpdateForm(status=TaskStatus.CANCELED.value),
    )
    logger_abrege.info(
        f"[Canceled task id : {id}][user id: {ctx.user_id}]",
        extra={"task_id": id, "user_id": ctx.user_id},
    )
    return updated


@router.delete("/task/{id}", response_model=TaskModel)
async def delete_task(
    id: str,
    ctx: RequestContext = Depends(TokenVerifier),
):
    task = task_table.get_task_by_id(task_id=id)
    if task is None or task.user_id != ctx.user_id:
        raise HTTPException(404, detail=f"{id} not found")
    if task.status in [
        TaskStatus.QUEUED,
        TaskStatus.STARTED,
        TaskStatus.IN_PROGRESS,
        TaskStatus.CREATED,
    ]:
        raise HTTPException(400, detail=f"{id} is active and cannot be deleted. Cancel it first.")

    task_table.delete_task_by_id(task_id=id)

    if task.type == "document":
        try:
            file_connector.delete_by_task_id(user_id=task.user_id, task_id=task.id)
        except FileNotFoundError:
            logger_abrege.warning(
                f"[File not found for task id : {task.id}]",
                extra={"task_id": task.id, "user_id": task.user_id},
            )
        except Exception as e:
            logger_abrege.exception(e, extra={"task_id": task.id, "user_id": task.user_id})

    ocr_task_ids = (task.output.extras or {}).get("task_ocr_id", []) if task.output is not None else []
    for ocr_task_id in ocr_task_ids if ocr_client is not None else []:
        try:
            ocr_client.delete_task(task_id=ocr_task_id)
        except Exception as e:
            logger_abrege.exception(
                e,
                extra={"task_id": task.id, "user_id": task.user_id, "ocr_task_id": ocr_task_id},
            )

    logger_abrege.debug(
        f"[Deleted task id : {task.id}][user id: {task.user_id}]",
        extra={"task_id": task.id, "user_id": task.user_id},
    )

    return task


def _get_owned_task(task_id: str, ctx: RequestContext) -> TaskModel:
    task = task_table.get_task_by_id(task_id=task_id)
    if task is None or task.user_id != ctx.user_id:
        raise HTTPException(404, detail=f"{task_id} not found")
    return task


def _get_task_or_404(task_id: str) -> TaskModel:
    """Existence check only, no ownership check — used by the internal (worker) endpoints,
    which act on behalf of the system rather than a specific end user."""
    task = task_table.get_task_by_id(task_id=task_id)
    if task is None:
        raise HTTPException(404, detail=f"{task_id} not found")
    return task


# ---------------------------------------------------------------------------
# Q&A items
# ---------------------------------------------------------------------------


class QAItemsChunkCreate(BaseModel):
    chunk_index: int
    qa_items: List[QAItem]


@router.get("/task/{id}/qa", response_model=List[QAItemRowModel])
async def get_task_qa_items(
    id: str,
    ctx: RequestContext = Depends(TokenVerifier),
) -> List[QAItemRowModel]:
    _get_owned_task(task_id=id, ctx=ctx)
    rows = qa_item_table.get_qa_items_by_task(task_id=id)
    return [QAItemRowModel.model_validate(row) for row in rows]


@router.get("/task/{id}/qa/{qa_item_id}", response_model=QAItemRowModel)
async def get_task_qa_item(
    id: str,
    qa_item_id: str,
    ctx: RequestContext = Depends(TokenVerifier),
) -> QAItemRowModel:
    _get_owned_task(task_id=id, ctx=ctx)
    row = qa_item_table.get_qa_item_by_id(task_id=id, qa_item_id=qa_item_id)
    if row is None:
        raise HTTPException(404, detail=f"{qa_item_id} not found")
    return QAItemRowModel.model_validate(row)


@router.post("/task/{id}/qa", status_code=201, dependencies=[Depends(verify_internal_service)])
async def create_task_qa_items(id: str, body: QAItemsChunkCreate):
    """Replace a chunk's Q&A items. Internal-only: called by the extraction worker, not end users."""
    _get_task_or_404(task_id=id)
    qa_item_table.save_chunk_qa_items(task_id=id, chunk_index=body.chunk_index, qa_items=body.qa_items)
    return {"task_id": id, "chunk_index": body.chunk_index, "status": "saved"}


@router.delete("/task/{id}/qa/{qa_item_id}")
async def delete_task_qa_item(
    id: str,
    qa_item_id: str,
    ctx: RequestContext = Depends(TokenVerifier),
):
    _get_owned_task(task_id=id, ctx=ctx)
    deleted = qa_item_table.delete_qa_item_by_id(task_id=id, qa_item_id=qa_item_id)
    if not deleted:
        raise HTTPException(404, detail=f"{qa_item_id} not found")
    return {"id": qa_item_id, "status": "deleted"}


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------


class EntitiesChunkCreate(BaseModel):
    chunk_index: int
    entities: List[EntityModel]
    relationships: List[RelationshipModel] = []


@router.get("/task/{id}/entities", response_model=List[EntityRowModel])
async def get_task_entities(
    id: str,
    ctx: RequestContext = Depends(TokenVerifier),
) -> List[EntityRowModel]:
    _get_owned_task(task_id=id, ctx=ctx)
    rows = entity_table.get_entities_by_task(task_id=id)
    return [EntityRowModel.model_validate(row) for row in rows]


@router.get("/task/{id}/entities/{entity_id}", response_model=EntityRowModel)
async def get_task_entity(
    id: str,
    entity_id: str,
    ctx: RequestContext = Depends(TokenVerifier),
) -> EntityRowModel:
    _get_owned_task(task_id=id, ctx=ctx)
    row = entity_table.get_entity_by_id(task_id=id, entity_id=entity_id)
    if row is None:
        raise HTTPException(404, detail=f"{entity_id} not found")
    return EntityRowModel.model_validate(row)


@router.post("/task/{id}/entities", status_code=201, dependencies=[Depends(verify_internal_service)])
async def create_task_entities(id: str, body: EntitiesChunkCreate):
    """Replace a chunk's entities and their local relationships (source_index/target_index
    resolved server-side against `entities`, in the same order). Internal-only."""
    _get_task_or_404(task_id=id)
    entity_table.save_chunk_entities(
        task_id=id,
        chunk_index=body.chunk_index,
        entities=body.entities,
        relationships=body.relationships,
    )
    return {"task_id": id, "chunk_index": body.chunk_index, "status": "saved"}


@router.delete("/task/{id}/entities/{entity_id}")
async def delete_task_entity(
    id: str,
    entity_id: str,
    ctx: RequestContext = Depends(TokenVerifier),
):
    _get_owned_task(task_id=id, ctx=ctx)
    deleted = entity_table.delete_entity_by_id(task_id=id, entity_id=entity_id)
    if not deleted:
        raise HTTPException(404, detail=f"{entity_id} not found")
    return {"id": entity_id, "status": "deleted"}


# ---------------------------------------------------------------------------
# Relationships
# ---------------------------------------------------------------------------


class GlobalRelationshipsCreate(BaseModel):
    entity_ids_in_order: List[str]
    relationships: List[RelationshipModel]


@router.get("/task/{id}/relationships", response_model=List[RelationshipRowModel])
async def get_task_relationships(
    id: str,
    ctx: RequestContext = Depends(TokenVerifier),
) -> List[RelationshipRowModel]:
    _get_owned_task(task_id=id, ctx=ctx)
    rows = entity_table.get_relationships_by_task(task_id=id)
    return [RelationshipRowModel.model_validate(row) for row in rows]


@router.get("/task/{id}/relationships/{relationship_id}", response_model=RelationshipRowModel)
async def get_task_relationship(
    id: str,
    relationship_id: str,
    ctx: RequestContext = Depends(TokenVerifier),
) -> RelationshipRowModel:
    _get_owned_task(task_id=id, ctx=ctx)
    row = entity_table.get_relationship_by_id(task_id=id, relationship_id=relationship_id)
    if row is None:
        raise HTTPException(404, detail=f"{relationship_id} not found")
    return RelationshipRowModel.model_validate(row)


@router.post("/task/{id}/relationships/global", status_code=201, dependencies=[Depends(verify_internal_service)])
async def create_task_global_relationships(id: str, body: GlobalRelationshipsCreate):
    """Replace the task's cross-chunk ("global") relationships — `source_index`/`target_index`
    resolved against `entity_ids_in_order`. Internal-only."""
    _get_task_or_404(task_id=id)
    entity_table.save_global_relationships(
        task_id=id,
        entity_ids_in_order=body.entity_ids_in_order,
        relationships=body.relationships,
    )
    return {"task_id": id, "status": "saved"}


@router.delete("/task/{id}/relationships/{relationship_id}")
async def delete_task_relationship(
    id: str,
    relationship_id: str,
    ctx: RequestContext = Depends(TokenVerifier),
):
    _get_owned_task(task_id=id, ctx=ctx)
    deleted = entity_table.delete_relationship_by_id(task_id=id, relationship_id=relationship_id)
    if not deleted:
        raise HTTPException(404, detail=f"{relationship_id} not found")
    return {"id": relationship_id, "status": "deleted"}


# ---------------------------------------------------------------------------
# Extraction trigger
# ---------------------------------------------------------------------------


@router.post("/task/{id}/extract-details", status_code=202)
async def extract_task_details(
    id: str,
    ctx: RequestContext = Depends(TokenVerifier),
):
    """Trigger (or retrigger) Q&A/entities/relationships extraction for a task, e.g. for
    tasks summarized before this feature existed or with `extract_qa=False` at the time."""
    task = _get_owned_task(task_id=id, ctx=ctx)
    if task.status != TaskStatus.COMPLETED:
        raise HTTPException(400, detail=f"{id} is not completed yet (status: {task.status})")
    if task.output is None or not task.output.texts_found:
        raise HTTPException(400, detail=f"{id} has no source text to extract details from")

    celery_app.send_task("worker.tasks.extract_task_details", args=[id])
    logger_abrege.info(
        f"[Extraction (re)triggered for task id : {id}][user id: {ctx.user_id}]",
        extra={"task_id": id, "user_id": ctx.user_id},
    )
    return {"task_id": id, "status": "extraction_queued"}
