from typing import List, Annotated
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, status as http_status
from fastapi.responses import JSONResponse
import json


from api.core.security.token import RequestContext
from api.core.security.factory import TokenVerifier

from src.schemas.task import (
    task_table,
    TaskModel,
    TaskStats,
    TaskStatus,
    TaskName,
    TaskForm,
)
from src.schemas.content import MergeModel
from src.schemas.pagination import Pagination
from src.clients import file_connector, celery_app
from src.utils.logger import logger_abrege
from src import __version__


router = APIRouter(tags=["Tasks"])

TokenDep = Annotated[RequestContext, Depends(TokenVerifier)]


@router.get("/task/{id}")
async def get_task(
    id: str,
    ctx: TokenDep,
    show_text_found: bool = False,
) -> TaskModel:
    task = task_table.get_task_by_id(task_id=id)
    if task is None or task.user_id != ctx.user_id:
        raise HTTPException(http_status.HTTP_404_NOT_FOUND, detail=f"{id} not found")
    logger_abrege.debug(
        f"[task id : {task.id}][user id: {task.user_id}]",
        extra={"task_id": task.id, "user_id": task.user_id},
    )
    task.position = task_table.get_position_in_queue(task_id=id)
    if not show_text_found and task.output is not None:
        task.output = task.output.model_copy()
        if task.output is not None:
            task.output.texts_found = []

    return task


@router.get("/tasks/stats")
async def get_statistics(
    ctx: TokenDep,
    skip: int = 0,
    limit: int = 10,
) -> TaskStats:
    try:
        stats = task_table.statistics(user_id=ctx.user_id, is_admin=bool(ctx.is_admin), skip=skip, limit=limit)
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


def read_user(user_id: str, offset: int = 1, limit: int = 10) -> List[TaskModel]:
    tmp_log = {"user_id": user_id}
    try:
        tasks = task_table.get_tasks_by_user_id(user_id=user_id, page=offset, page_size=limit)
        logger_abrege.debug(f"[Task found: {len(tasks)}]", extra=tmp_log)
        if tasks is None:
            raise HTTPException(http_status.HTTP_404_NOT_FOUND, detail=f"{user_id} not found")
    except Exception as e:
        logger_abrege.error(e, extra=tmp_log)
        raise HTTPException(http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{str(e)} not found")

    return tasks


@router.get("/task/user/")
async def get_tasks_read_user(
    ctx: TokenDep,
    offset: int = 1,
    limit: int = 10,
) -> Pagination[TaskModel]:
    tasks = read_user(user_id=ctx.user_id, offset=offset, limit=limit)
    total = task_table.count_tasks_by_user_id(user_id=ctx.user_id)
    return Pagination[TaskModel](total=total, page=offset, page_size=limit, items=tasks)


@router.delete("/task/{id}", status_code=http_status.HTTP_204_NO_CONTENT)
async def delete_task(id: str, ctx: TokenDep):
    task = task_table.delete_task_by_id(task_id=id)
    if task is None or task.user_id != ctx.user_id:
        raise HTTPException(http_status.HTTP_404_NOT_FOUND, detail=f"{id} not found")
    if task.status in ["queued", "started", "in_progress"]:
        raise HTTPException(
            http_status.HTTP_400_BAD_REQUEST,
            detail=f"{id} is queued and cannot be deleted",
        )

    try:
        file_connector.delete_by_task_id(user_id=task.user_id, task_id=task.id)
    except Exception as e:
        logger_abrege.exception(e, extra={"task_id": task.id, "user_id": task.user_id})

    logger_abrege.debug(
        f"[Deleted task id : {task.id}][user id: {task.user_id}]",
        extra={"task_id": task.id, "user_id": task.user_id},
    )


@router.post("/tasks/merge/", status_code=http_status.HTTP_201_CREATED)
async def merge_tasks(
    task_ids: List[str],
    ctx: TokenDep,
) -> TaskModel:
    tasks = []
    for task_id in task_ids:
        task = task_table.get_task_by_id(task_id=task_id)
        if task is None or task.user_id != ctx.user_id:
            raise HTTPException(http_status.HTTP_404_NOT_FOUND, detail=f"{task_id} not found")
        if task.status != TaskStatus.COMPLETED.value:
            raise HTTPException(
                http_status.HTTP_400_BAD_REQUEST,
                detail=f"{task_id} is not completed and cannot be merged",
            )
        tasks.append(task)

    new_task = TaskForm(
        user_id=ctx.user_id,
        input=MergeModel(task_ids=task_ids),
        output=None,
        status=TaskStatus.QUEUED.value,
        type="merge",
        created_at=int(datetime.now().timestamp()),
        model_name="merge",
        model_version=__version__,
    )
    new_task = task_table.insert_new_task(user_id=new_task.user_id, form_data=new_task)
    if new_task is None:
        raise HTTPException(
            http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create merge task",
        )

    celery_app.send_task(
        name=TaskName.MERGE.value,
        args=[json.dumps(new_task.model_dump())],
        task_id=new_task.id,
    )

    return new_task
