from typing import List, Annotated
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, status as http_status
from fastapi.responses import JSONResponse


from api.core.security.token import RequestContext
from api.core.security.factory import TokenVerifier
from src.services.merge_task_service import merge_task_service
from src.models.merge_task import MergeTaskCreateForm

from src.schemas.task import task_table
from src.models.task import (
    TaskModel,
    TaskStats,
    TaskStatus,
    TaskForm,
    TaskUpdateForm,
)
from src.schemas.content import MergeModel
from src.schemas.pagination import Pagination
from src.clients import file_connector, celery_app
from src.utils.logger import logger_abrege
from src.internal.db import get_async_session_dep
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.task_service import TaskService


router = APIRouter(tags=["Tasks"])

TokenDep = Annotated[RequestContext, Depends(TokenVerifier)]
DbDep = Annotated[AsyncSession, Depends(get_async_session_dep)]
TaskServiceDep = Annotated[TaskService, Depends(TaskService)]


@router.get("/task/{id}")
async def get_task(
    id: str,
    ctx: TokenDep,
    db: DbDep,
    service: TaskServiceDep,
    show_text_found: bool = False,
) -> TaskModel:
    task = await service.get_task_by_id(db=db, task_id=id)
    if task is None or task.user_id != ctx.user_id:
        raise HTTPException(http_status.HTTP_404_NOT_FOUND, detail=f"{id} not found")
    with logger_abrege.contextualize(  # ty:ignore[unresolved-attribute]
        task_id=task.id, user_id=task.user_id
    ):
        logger_abrege.debug(f"Task retrieved with status: {task.status}")

    task.position = await service.get_position_in_queue(db=db, task_id=id)
    if not show_text_found and task.output is not None:
        task.output = task.output.model_copy()
        if task.output is not None:
            task.output.texts_found = []

    return task


@router.get("/tasks/stats")
async def get_statistics(
    ctx: TokenDep,
    db: DbDep,
    service: TaskServiceDep,
    skip: int = 0,
    limit: int = 10,
) -> TaskStats:
    if ctx.user_id is None:
        raise HTTPException(status_code=http_status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    try:
        stats = await service.get_statistics(
            db=db,
            user_id=ctx.user_id,
            is_admin=bool(ctx.is_admin),
            skip=skip,
            limit=limit,
        )
        return stats
    except Exception as e:
        logger_abrege.exception(e, extra={"user_id": ctx.user_id})
        raise HTTPException(http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/tasks/count-users-today")
async def get_unique_users_today(
    ctx: TokenDep,
) -> JSONResponse:
    try:
        now = datetime.now()
        start = int(datetime(now.year, now.month, now.day).timestamp())
        end = start + 24 * 60 * 60
        count = task_table.count_unique_users_between_dates(start_date=start, end_date=end)
        return JSONResponse({"users_today": count})
    except Exception as e:
        logger_abrege.exception(e, extra={"user_id": ctx.user_id})
        raise HTTPException(http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


async def read_user(
    service: TaskService,
    db: AsyncSession,
    user_id: str,
    offset: int = 1,
    limit: int = 10,
) -> List[TaskModel]:
    tmp_log = {"user_id": user_id}
    try:
        tasks = await service.get_tasks_by_user_id(db=db, user_id=user_id, page=offset, page_size=limit)
        logger_abrege.debug(f"[Task found: {len(tasks)}]", extra=tmp_log)
    except Exception as e:
        logger_abrege.error(e, extra=tmp_log)
        raise HTTPException(http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{str(e)} not found")

    return tasks


@router.get("/task/user/")
async def get_tasks_read_user(
    ctx: TokenDep,
    db: DbDep,
    service: TaskServiceDep,
    offset: int = 1,
    limit: int = 10,
) -> Pagination[TaskModel]:
    if ctx.user_id is None:
        raise HTTPException(status_code=http_status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    tasks = await read_user(service=service, db=db, user_id=ctx.user_id, offset=offset, limit=limit)
    total = await service.count_tasks_by_user_id(db=db, user_id=ctx.user_id)
    return Pagination[TaskModel](total=total, page=offset, page_size=limit, items=tasks)


@router.put("/task/{id}")
async def update_task(
    id: str,
    form_data: TaskUpdateForm,
    ctx: TokenDep,
    db: DbDep,
    service: TaskServiceDep,
) -> TaskModel:
    task = await service.get_task_by_id(db=db, task_id=id)
    if task is None or task.user_id != ctx.user_id:
        raise HTTPException(http_status.HTTP_404_NOT_FOUND, detail=f"{id} not found")
    updated = await service.update_task(db=db, task_id=id, form_data=form_data)
    if updated is None:
        raise HTTPException(http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Update failed")
    return updated


@router.delete("/task/{id}", status_code=http_status.HTTP_204_NO_CONTENT)
async def delete_task(
    id: str,
    ctx: TokenDep,
    db: DbDep,
    service: TaskServiceDep,
):
    task = await service.get_task_by_id(db=db, task_id=id)
    if task is None or task.user_id != ctx.user_id:
        raise HTTPException(http_status.HTTP_404_NOT_FOUND, detail=f"{id} not found")
    if task.status in [
        TaskStatus.QUEUED.value,
        TaskStatus.STARTED.value,
        TaskStatus.IN_PROGRESS.value,
    ]:
        raise HTTPException(
            http_status.HTTP_400_BAD_REQUEST,
            detail=f"{id} is queued and cannot be deleted",
        )

    with logger_abrege.contextualize(  # ty:ignore[unresolved-attribute]
        task_id=task.id, user_id=task.user_id
    ):
        try:
            await service.delete_task_by_id(db=db, task_id=id)
            file_connector.delete_by_task_id(user_id=task.user_id, task_id=task.id)
            logger_abrege.info("Task and associated files deleted successfully")
        except Exception as e:
            logger_abrege.exception(e)


@router.delete("/task/{id}/revoke", status_code=http_status.HTTP_204_NO_CONTENT)
async def revoke_task(
    id: str,
    ctx: TokenDep,
    db: DbDep,
    service: TaskServiceDep,
):
    task = await service.get_task_by_id(db=db, task_id=id)
    if task is None or task.user_id != ctx.user_id:
        raise HTTPException(http_status.HTTP_404_NOT_FOUND, detail=f"{id} not found")
    if task.status not in [
        TaskStatus.QUEUED.value,
        TaskStatus.STARTED.value,
        TaskStatus.IN_PROGRESS.value,
    ]:
        raise HTTPException(
            http_status.HTTP_400_BAD_REQUEST,
            detail=f"{id} is not queued and cannot be revoked",
        )
    celery_app.control.revoke(id, terminate=True)
    await service.update_task(
        db=db,
        task_id=id,
        form_data=TaskUpdateForm(status=TaskStatus.REVOKED.value),
    )


@router.post("/tasks/merge/", status_code=http_status.HTTP_201_CREATED)
async def merge_tasks(
    task_ids: List[str],
    ctx: TokenDep,
    db: DbDep,
    service: TaskServiceDep,
) -> TaskModel:
    if ctx.user_id is None:
        raise HTTPException(status_code=http_status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    new_task_form = TaskForm(
        input=MergeModel(task_ids=task_ids, created_at=int(datetime.now().timestamp())),
        output=None,
        status=TaskStatus.QUEUED.value,
        type="merge",
    )
    new_task = await service.insert_new_task(db=db, user_id=ctx.user_id, form_data=new_task_form)

    for task_id in task_ids:
        merge_task_service.create_merge_task(
            merge_task_create=MergeTaskCreateForm(
                related_task=task_id,
                merge_id=new_task.id,
                type="document",
                user_id=ctx.user_id,
                group_id=ctx.user_id,
            )
        )

    return new_task
