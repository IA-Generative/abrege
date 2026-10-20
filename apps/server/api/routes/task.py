import os
from typing import Annotated, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field


from api.core.security.token import RequestContext
from api.docs import (
    INTERNAL_SECURITY,
    INTERNAL_UNAUTHORIZED,
    ITEM_NOT_FOUND,
    TASK_NOT_FOUND,
    TASK_NOT_FOUND_INTERNAL,
    UNAUTHORIZED,
    ChunkId,
    EntityId,
    ErrorResponse,
    PageNumber,
    PageSize,
    QAItemId,
    RelationshipId,
    TaskId,
    TopicId,
    USER_SECURITY,
)
from api.core.security.factory import TokenVerifier
from api.core.security.internal import verify_internal_service

from src.schemas.task import task_table, TaskModel, TaskUpdateForm, TaskStatus
from src.schemas.pagination import Pagination
from src.schemas.code_error import TASK_STATUS_TO_HTTP
from src.schemas.qa_item import qa_item_table, QAItemRowModel
from src.schemas.entity import entity_table, EntityRowModel, RelationshipRowModel
from src.schemas.topic import topic_table, TopicRowModel
from src.schemas.chunk import chunk_table, ChunkRowModel
from src.schemas.result import EntityModel, QAItem, RelationshipModel, TopicModel
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

router = APIRouter()


@router.get(
    "/task/{id}",
    response_model=TaskModel,
    tags=["Tasks"],
    summary="Get a task",
    description="""Return a task with its input, parameters and, once finished, its output (the summary is in `output.summary`).

**The HTTP status code mirrors the task state**, so a client can poll without reading the body:

| `status` | HTTP code |
|---|---|
| `created` | 201 |
| `queued`, `started` | 202 |
| `in_progress` | 206 |
| `completed` | 200 |
| `retrying` | 208 |
| `failed`, `canceled` | 500 |
| `timeout` | 504 |

`position` is the rank in the processing queue while the task waits. The side extractions
(Q&A, entities, chunks, topics) have their own `*_status` fields, independent of `status`.""",
    responses={201: {"model": TaskModel, "description": "Task created, not queued yet."},
        202: {"model": TaskModel, "description": "Task queued or started."},
        206: {"model": TaskModel, "description": "Task in progress."},
        208: {"model": TaskModel, "description": "Task is being retried after a failure."},
        500: {"model": TaskModel, "description": "Task failed or was canceled."},
        504: {"model": TaskModel, "description": "Task timed out."},
        **UNAUTHORIZED,
        **TASK_NOT_FOUND},
    openapi_extra={"security": USER_SECURITY},
)
async def get_task(
    id: TaskId,
    show_text_found: Annotated[bool, Query(description="Include the extracted source text in `output.texts_found`. Left out by default because it can be large.")] = False,
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


@router.get(
    "/task/user/",
    response_model=Pagination[TaskModel],
    tags=["Tasks"],
    summary="List my tasks",
    description="""List the tasks of the authenticated user. Paginated: `offset` is the page number (1-based) and `limit` the page size.""",
    responses={**UNAUTHORIZED},
    openapi_extra={"security": USER_SECURITY},
)
async def get_tasks_read_user(
    offset: PageNumber = 1,
    limit: PageSize = 10,
    ctx: RequestContext = Depends(TokenVerifier),
) -> Pagination[TaskModel]:
    tasks = read_user(user_id=ctx.user_id, offset=offset, limit=limit)
    total = task_table.count_tasks_by_user_id(user_id=ctx.user_id)
    return Pagination[TaskModel](total=total, page=offset, page_size=limit, items=tasks)


@router.post(
    "/task/{id}/cancel",
    response_model=TaskModel,
    tags=["Tasks"],
    summary="Cancel a task",
    description="""Cancel a task that has not finished yet (`created`, `queued`, `started` or `in_progress`). Its processing is
revoked and its status becomes `canceled`.""",
    responses={400: {"model": ErrorResponse, "description": "The task is already finished and cannot be canceled."},
        **UNAUTHORIZED,
        **TASK_NOT_FOUND},
    openapi_extra={"security": USER_SECURITY},
)
async def cancel_task(
    id: TaskId,
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


@router.delete(
    "/task/{id}",
    response_model=TaskModel,
    tags=["Tasks"],
    summary="Delete a task",
    description="""Delete a finished task together with its stored file and OCR data. An active task (`created`, `queued`, `started` or
`in_progress`) must be canceled first. Returns the deleted task.""",
    responses={400: {"model": ErrorResponse, "description": "The task is still active: cancel it first."},
        **UNAUTHORIZED,
        **TASK_NOT_FOUND},
    openapi_extra={"security": USER_SECURITY},
)
async def delete_task(
    id: TaskId,
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
    chunk_index: int = Field(description="Index of the chunk the items belong to")
    qa_items: List[QAItem] = Field(description="Question/answer pairs to store (replaces the chunk's previous ones)")
    model_name: Optional[str] = Field(None, description="LLM that generated the pairs")


@router.get(
    "/task/{id}/qa",
    response_model=Pagination[QAItemRowModel],
    tags=["Task results"],
    summary="List question/answer pairs",
    description="""Question/answer pairs generated from the task's source text (requires `extract_qa`). Paginated: `offset` is the page number (1-based) and `limit` the page size.""",
    responses={**UNAUTHORIZED, **TASK_NOT_FOUND},
    openapi_extra={"security": USER_SECURITY},
)
async def get_task_qa_items(
    id: TaskId,
    offset: PageNumber = 1,
    limit: PageSize = 20,
    ctx: RequestContext = Depends(TokenVerifier),
) -> Pagination[QAItemRowModel]:
    _get_owned_task(task_id=id, ctx=ctx)
    rows = qa_item_table.get_qa_items_by_task_paginated(task_id=id, page=offset, page_size=limit)
    total = qa_item_table.count_qa_items_by_task(task_id=id)
    return Pagination[QAItemRowModel](
        total=total, page=offset, page_size=limit, items=[QAItemRowModel.model_validate(row) for row in rows]
    )


@router.get(
    "/task/{id}/qa/{qa_item_id}",
    response_model=QAItemRowModel,
    tags=["Task results"],
    summary="Get a question/answer pair",
    description="""Return one question/answer pair of the task.""",
    responses={**UNAUTHORIZED, **ITEM_NOT_FOUND},
    openapi_extra={"security": USER_SECURITY},
)
async def get_task_qa_item(
    id: TaskId,
    qa_item_id: QAItemId,
    ctx: RequestContext = Depends(TokenVerifier),
) -> QAItemRowModel:
    _get_owned_task(task_id=id, ctx=ctx)
    row = qa_item_table.get_qa_item_by_id(task_id=id, qa_item_id=qa_item_id)
    if row is None:
        raise HTTPException(404, detail=f"{qa_item_id} not found")
    return QAItemRowModel.model_validate(row)


@router.post(
    "/task/{id}/qa",
    status_code=201,
    tags=["Internal (worker)"],
    summary="Store a chunk's question/answer pairs",
    description="""Replace the question/answer pairs of one chunk. **Internal only**: called by the extraction worker, not by end users.""",
    responses={**INTERNAL_UNAUTHORIZED, **TASK_NOT_FOUND_INTERNAL},
    openapi_extra={"security": INTERNAL_SECURITY},
    dependencies=[Depends(verify_internal_service)],
)
async def create_task_qa_items(id: TaskId, body: QAItemsChunkCreate):
    """Replace a chunk's Q&A items. Internal-only: called by the extraction worker, not end users."""
    _get_task_or_404(task_id=id)
    qa_item_table.save_chunk_qa_items(
        task_id=id, chunk_index=body.chunk_index, qa_items=body.qa_items, model_name=body.model_name
    )
    return {"task_id": id, "chunk_index": body.chunk_index, "status": "saved"}


@router.delete(
    "/task/{id}/qa/{qa_item_id}",
    tags=["Task results"],
    summary="Delete a question/answer pair",
    description="""Delete one question/answer pair of the task.""",
    responses={**UNAUTHORIZED, **ITEM_NOT_FOUND},
    openapi_extra={"security": USER_SECURITY},
)
async def delete_task_qa_item(
    id: TaskId,
    qa_item_id: QAItemId,
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
    chunk_index: int = Field(description="Index of the chunk the entities belong to")
    entities: List[EntityModel] = Field(description="Entities to store (replaces the chunk's previous ones)")
    relationships: List[RelationshipModel] = Field(default_factory=list, description="Local relationships between `entities`, by index")
    model_name: Optional[str] = Field(None, description="LLM that extracted them")


@router.get(
    "/task/{id}/entities",
    response_model=Pagination[EntityRowModel],
    tags=["Task results"],
    summary="List entities",
    description="""Entities extracted from the task's source text (requires `extract_entities`). When `entity_definitions` was given, only entities matching a definition are extracted, and `type` is the definition name. Paginated: `offset` is the page number (1-based) and `limit` the page size.""",
    responses={**UNAUTHORIZED, **TASK_NOT_FOUND},
    openapi_extra={"security": USER_SECURITY},
)
async def get_task_entities(
    id: TaskId,
    offset: PageNumber = 1,
    limit: PageSize = 20,
    ctx: RequestContext = Depends(TokenVerifier),
) -> Pagination[EntityRowModel]:
    _get_owned_task(task_id=id, ctx=ctx)
    rows = entity_table.get_entities_by_task_paginated(task_id=id, page=offset, page_size=limit)
    total = entity_table.count_entities_by_task(task_id=id)
    return Pagination[EntityRowModel](
        total=total, page=offset, page_size=limit, items=[EntityRowModel.model_validate(row) for row in rows]
    )


@router.get(
    "/task/{id}/entities/{entity_id}",
    response_model=EntityRowModel,
    tags=["Task results"],
    summary="Get an entity",
    description="""Return one entity of the task.""",
    responses={**UNAUTHORIZED, **ITEM_NOT_FOUND},
    openapi_extra={"security": USER_SECURITY},
)
async def get_task_entity(
    id: TaskId,
    entity_id: EntityId,
    ctx: RequestContext = Depends(TokenVerifier),
) -> EntityRowModel:
    _get_owned_task(task_id=id, ctx=ctx)
    row = entity_table.get_entity_by_id(task_id=id, entity_id=entity_id)
    if row is None:
        raise HTTPException(404, detail=f"{entity_id} not found")
    return EntityRowModel.model_validate(row)


@router.post(
    "/task/{id}/entities",
    status_code=201,
    tags=["Internal (worker)"],
    summary="Store a chunk's entities",
    description="""Replace the entities of one chunk and their local relationships. `source_index` and `target_index` of each relationship are resolved
server-side against `entities`, in the same order. **Internal only**: called by the extraction worker.""",
    responses={**INTERNAL_UNAUTHORIZED, **TASK_NOT_FOUND_INTERNAL},
    openapi_extra={"security": INTERNAL_SECURITY},
    dependencies=[Depends(verify_internal_service)],
)
async def create_task_entities(id: TaskId, body: EntitiesChunkCreate):
    """Replace a chunk's entities and their local relationships (source_index/target_index
    resolved server-side against `entities`, in the same order). Internal-only."""
    _get_task_or_404(task_id=id)
    entity_table.save_chunk_entities(
        task_id=id,
        chunk_index=body.chunk_index,
        entities=body.entities,
        relationships=body.relationships,
        model_name=body.model_name,
    )
    return {"task_id": id, "chunk_index": body.chunk_index, "status": "saved"}


@router.delete(
    "/task/{id}/entities/{entity_id}",
    tags=["Task results"],
    summary="Delete an entity",
    description="""Delete one entity of the task.""",
    responses={**UNAUTHORIZED, **ITEM_NOT_FOUND},
    openapi_extra={"security": USER_SECURITY},
)
async def delete_task_entity(
    id: TaskId,
    entity_id: EntityId,
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
    entity_ids_in_order: List[str] = Field(description="Entity identifiers; `source_index`/`target_index` of the relationships refer to this list")
    relationships: List[RelationshipModel] = Field(description="Cross-chunk relationships to store (replaces the previous ones)")
    model_name: Optional[str] = Field(None, description="LLM that inferred them")


@router.get(
    "/task/{id}/relationships",
    response_model=Pagination[RelationshipRowModel],
    tags=["Task results"],
    summary="List relationships",
    description="""Relationships between the task's entities (requires `extract_entities`). `chunk_index` is `null` for cross-chunk (global) relationships. Paginated: `offset` is the page number (1-based) and `limit` the page size.""",
    responses={**UNAUTHORIZED, **TASK_NOT_FOUND},
    openapi_extra={"security": USER_SECURITY},
)
async def get_task_relationships(
    id: TaskId,
    offset: PageNumber = 1,
    limit: PageSize = 20,
    ctx: RequestContext = Depends(TokenVerifier),
) -> Pagination[RelationshipRowModel]:
    _get_owned_task(task_id=id, ctx=ctx)
    rows = entity_table.get_relationships_by_task_paginated(task_id=id, page=offset, page_size=limit)
    total = entity_table.count_relationships_by_task(task_id=id)
    return Pagination[RelationshipRowModel](
        total=total, page=offset, page_size=limit, items=[RelationshipRowModel.model_validate(row) for row in rows]
    )


@router.get(
    "/task/{id}/relationships/{relationship_id}",
    response_model=RelationshipRowModel,
    tags=["Task results"],
    summary="Get a relationship",
    description="""Return one relationship of the task.""",
    responses={**UNAUTHORIZED, **ITEM_NOT_FOUND},
    openapi_extra={"security": USER_SECURITY},
)
async def get_task_relationship(
    id: TaskId,
    relationship_id: RelationshipId,
    ctx: RequestContext = Depends(TokenVerifier),
) -> RelationshipRowModel:
    _get_owned_task(task_id=id, ctx=ctx)
    row = entity_table.get_relationship_by_id(task_id=id, relationship_id=relationship_id)
    if row is None:
        raise HTTPException(404, detail=f"{relationship_id} not found")
    return RelationshipRowModel.model_validate(row)


@router.post(
    "/task/{id}/relationships/global",
    status_code=201,
    tags=["Internal (worker)"],
    summary="Store the global relationships",
    description="""Replace the task's cross-chunk (global) relationships; `source_index` and `target_index` are resolved against `entity_ids_in_order`.
**Internal only**: called by the extraction worker.""",
    responses={**INTERNAL_UNAUTHORIZED, **TASK_NOT_FOUND_INTERNAL},
    openapi_extra={"security": INTERNAL_SECURITY},
    dependencies=[Depends(verify_internal_service)],
)
async def create_task_global_relationships(id: TaskId, body: GlobalRelationshipsCreate):
    """Replace the task's cross-chunk ("global") relationships — `source_index`/`target_index`
    resolved against `entity_ids_in_order`. Internal-only."""
    _get_task_or_404(task_id=id)
    entity_table.save_global_relationships(
        task_id=id,
        entity_ids_in_order=body.entity_ids_in_order,
        relationships=body.relationships,
        model_name=body.model_name,
    )
    return {"task_id": id, "status": "saved"}


@router.delete(
    "/task/{id}/relationships/{relationship_id}",
    tags=["Task results"],
    summary="Delete a relationship",
    description="""Delete one relationship of the task.""",
    responses={**UNAUTHORIZED, **ITEM_NOT_FOUND},
    openapi_extra={"security": USER_SECURITY},
)
async def delete_task_relationship(
    id: TaskId,
    relationship_id: RelationshipId,
    ctx: RequestContext = Depends(TokenVerifier),
):
    _get_owned_task(task_id=id, ctx=ctx)
    deleted = entity_table.delete_relationship_by_id(task_id=id, relationship_id=relationship_id)
    if not deleted:
        raise HTTPException(404, detail=f"{relationship_id} not found")
    return {"id": relationship_id, "status": "deleted"}


# ---------------------------------------------------------------------------
# Topics (free-form classification of the final summary)
# ---------------------------------------------------------------------------


class TopicsCreate(BaseModel):
    topics: List[TopicModel] = Field(description="Topics to store (replaces every previous topic of the task)")
    model_name: Optional[str] = Field(None, description="LLM that classified the document")


@router.get(
    "/task/{id}/topics",
    response_model=Pagination[TopicRowModel],
    tags=["Task results"],
    summary="List topics",
    description="""Topics the document was classified into, most confident first (requires `classify_topics`). When `topic_definitions` was given, the classification is steered towards them. Paginated: `offset` is the page number (1-based) and `limit` the page size.""",
    responses={**UNAUTHORIZED, **TASK_NOT_FOUND},
    openapi_extra={"security": USER_SECURITY},
)
async def get_task_topics(
    id: TaskId,
    offset: PageNumber = 1,
    limit: PageSize = 20,
    ctx: RequestContext = Depends(TokenVerifier),
) -> Pagination[TopicRowModel]:
    _get_owned_task(task_id=id, ctx=ctx)
    rows = topic_table.get_topics_by_task_paginated(task_id=id, page=offset, page_size=limit)
    total = topic_table.count_topics_by_task(task_id=id)
    return Pagination[TopicRowModel](
        total=total, page=offset, page_size=limit, items=[TopicRowModel.model_validate(row) for row in rows]
    )


@router.post(
    "/task/{id}/topics",
    status_code=201,
    tags=["Internal (worker)"],
    summary="Store the topics",
    description="""Replace every topic of the task. **Internal only**: called by the classification worker.""",
    responses={**INTERNAL_UNAUTHORIZED, **TASK_NOT_FOUND_INTERNAL},
    openapi_extra={"security": INTERNAL_SECURITY},
    dependencies=[Depends(verify_internal_service)],
)
async def create_task_topics(id: TaskId, body: TopicsCreate):
    """Replace every topic for the task. Internal-only: called by the classification worker."""
    _get_task_or_404(task_id=id)
    topic_table.save_topics(task_id=id, topics=body.topics, model_name=body.model_name)
    return {"task_id": id, "status": "saved"}


@router.delete(
    "/task/{id}/topics/{topic_id}",
    tags=["Task results"],
    summary="Delete a topic",
    description="""Delete one topic of the task.""",
    responses={**UNAUTHORIZED, **ITEM_NOT_FOUND},
    openapi_extra={"security": USER_SECURITY},
)
async def delete_task_topic(
    id: TaskId,
    topic_id: TopicId,
    ctx: RequestContext = Depends(TokenVerifier),
):
    _get_owned_task(task_id=id, ctx=ctx)
    deleted = topic_table.delete_topic_by_id(task_id=id, topic_id=topic_id)
    if not deleted:
        raise HTTPException(404, detail=f"{topic_id} not found")
    return {"id": topic_id, "status": "deleted"}


# ---------------------------------------------------------------------------
# Chunks (semantic chunking of the source text, done LLM-side at map time)
# ---------------------------------------------------------------------------


class ChunksCreate(BaseModel):
    chunk_index: int = Field(description="Index of the map-step window the chunks belong to")
    page: Optional[int] = Field(None, description="Source page, when known")
    chunks: List[str] = Field(description="Texts of the semantic chunks, in order")
    model_name: Optional[str] = Field(None, description="LLM that produced the chunking")


@router.get(
    "/task/{id}/chunks",
    response_model=Pagination[ChunkRowModel],
    tags=["Task results"],
    summary="List semantic chunks",
    description="""Semantic sub-chunks the source text was split into while summarizing (requires `extract_chunks`), in reading order. Paginated: `offset` is the page number (1-based) and `limit` the page size.""",
    responses={**UNAUTHORIZED, **TASK_NOT_FOUND},
    openapi_extra={"security": USER_SECURITY},
)
async def get_task_chunks(
    id: TaskId,
    offset: PageNumber = 1,
    limit: PageSize = 20,
    ctx: RequestContext = Depends(TokenVerifier),
) -> Pagination[ChunkRowModel]:
    _get_owned_task(task_id=id, ctx=ctx)
    rows = chunk_table.get_chunks_by_task_paginated(task_id=id, page=offset, page_size=limit)
    total = chunk_table.count_chunks_by_task(task_id=id)
    return Pagination[ChunkRowModel](
        total=total, page=offset, page_size=limit, items=[ChunkRowModel.model_validate(row) for row in rows]
    )


@router.get(
    "/task/{id}/chunks/{chunk_id}",
    response_model=ChunkRowModel,
    tags=["Task results"],
    summary="Get a chunk",
    description="""Return one semantic chunk of the task.""",
    responses={**UNAUTHORIZED, **ITEM_NOT_FOUND},
    openapi_extra={"security": USER_SECURITY},
)
async def get_task_chunk(
    id: TaskId,
    chunk_id: ChunkId,
    ctx: RequestContext = Depends(TokenVerifier),
) -> ChunkRowModel:
    _get_owned_task(task_id=id, ctx=ctx)
    row = chunk_table.get_chunk_by_id(task_id=id, chunk_id=chunk_id)
    if row is None:
        raise HTTPException(404, detail=f"{chunk_id} not found")
    return ChunkRowModel.model_validate(row)


@router.post(
    "/task/{id}/chunks",
    status_code=201,
    tags=["Internal (worker)"],
    summary="Store a window's semantic chunks",
    description="""Replace the semantic sub-chunks of one map-step window. **Internal only**: called by the extraction worker.""",
    responses={**INTERNAL_UNAUTHORIZED, **TASK_NOT_FOUND_INTERNAL},
    openapi_extra={"security": INTERNAL_SECURITY},
    dependencies=[Depends(verify_internal_service)],
)
async def create_task_chunks(id: TaskId, body: ChunksCreate):
    """Replace the semantic sub-chunks for one map-step window. Internal-only: called by the
    extraction worker right as it sends that window's text to the chunking model."""
    _get_task_or_404(task_id=id)
    chunk_table.save_chunk_group(
        task_id=id, chunk_index=body.chunk_index, page=body.page, chunks=body.chunks, model_name=body.model_name
    )
    return {"task_id": id, "chunk_index": body.chunk_index, "status": "saved"}


@router.delete(
    "/task/{id}/chunks/{chunk_id}",
    tags=["Task results"],
    summary="Delete a chunk",
    description="""Delete one semantic chunk of the task.""",
    responses={**UNAUTHORIZED, **ITEM_NOT_FOUND},
    openapi_extra={"security": USER_SECURITY},
)
async def delete_task_chunk(
    id: TaskId,
    chunk_id: ChunkId,
    ctx: RequestContext = Depends(TokenVerifier),
):
    _get_owned_task(task_id=id, ctx=ctx)
    deleted = chunk_table.delete_chunk_by_id(task_id=id, chunk_id=chunk_id)
    if not deleted:
        raise HTTPException(404, detail=f"{chunk_id} not found")
    return {"id": chunk_id, "status": "deleted"}


# ---------------------------------------------------------------------------
# Extraction trigger
# ---------------------------------------------------------------------------


@router.post(
    "/task/{id}/extract-details",
    status_code=202,
    tags=["Tasks"],
    summary="(Re)trigger the extractions",
    description="""Trigger, or re-trigger, the Q&A, entities, relationships and chunks extraction for a task that is already `completed`,
for instance a task summarized before these extractions existed or without them requested. Runs in the background:
follow `qa_entities_status` and `relationships_status` on the task, then read the results.""",
    responses={400: {"model": ErrorResponse, "description": "The task is not completed yet, or has no source text to extract from."},
        **UNAUTHORIZED,
        **TASK_NOT_FOUND},
    openapi_extra={"security": USER_SECURITY},
)
async def extract_task_details(
    id: TaskId,
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
