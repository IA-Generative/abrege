from typing import List
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse


from api.core.security.token import RequestContext
from api.core.security.factory import TokenVerifier

from src.schemas.task import task_table, TaskModel, TaskStats
from src.schemas.pagination import Pagination
from src.schemas.code_error import TASK_STATUS_TO_HTTP
from src.clients import file_connector
from src.utils.logger import logger_abrege


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


@router.get("/task/stats", response_model=TaskStats)
async def get_statistics(
    skip: int = 0,
    limit: int = 10,
    ctx: RequestContext = Depends(TokenVerifier),
) -> TaskStats:
    try:
        stats = task_table.statistics(user_id=ctx.user_id, is_admin=bool(
            ctx.is_admin), skip=skip, limit=limit)
        return stats
    except Exception as e:
        logger_abrege.exception(e, extra={"user_id": ctx.user_id})
        raise HTTPException(500, detail=str(e))


@router.get("/task/unique_users")
async def get_unique_users_today(
    ctx: RequestContext = Depends(TokenVerifier),
) -> JSONResponse:
    try:
        now = datetime.now()
        start = int(datetime(now.year, now.month, now.day).timestamp())
        end = start + 24 * 60 * 60
        count = task_table.count_unique_users_between_dates(
            start_date=start, end_date=end)
        return JSONResponse({"users_today": count})
    except Exception as e:
        logger_abrege.exception(e, extra={"user_id": ctx.user_id})
        raise HTTPException(500, detail=str(e))


def read_user(user_id: str, offset: int = 1, limit: int = 10) -> List[TaskModel]:
    tmp_log = {"user_id": user_id}
    try:
        tasks = task_table.get_tasks_by_user_id(
            user_id=user_id, page=offset, page_size=limit)
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


@router.delete("/task/{id}", status_code=204)
async def delete_task(
    id: str,
    ctx: RequestContext = Depends(TokenVerifier),
):
    task = task_table.delete_task_by_id(task_id=id)
    if task is None or task.user_id != ctx.user_id:
        raise HTTPException(404, detail=f"{id} not found")
    if task.status in ["queued", "started", "in_progress"]:
        raise HTTPException(400, detail=f"{id} is queued and cannot be deleted")

    try:
        file_connector.delete_by_task_id(user_id=task.user_id, task_id=task.id)
    except Exception as e:
        logger_abrege.exception(e, extra={"task_id": task.id, "user_id": task.user_id})

    logger_abrege.debug(
        f"[Deleted task id : {task.id}][user id: {task.user_id}]",
        extra={"task_id": task.id, "user_id": task.user_id},
    )
