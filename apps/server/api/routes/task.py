from typing import List
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse

from src.schemas.task import task_table, TaskModel
from src.schemas.code_error import TASK_STATUS_TO_HTTP
from src.utils.logger import logger_abrege
from api.core.security.token import RequestContext
from api.core.security.factory import TokenVerifier


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


@router.get("/task/user/", response_model=List[TaskModel])
async def get_tasks_read_user(
    offset: int = 1,
    limit: int = 10,
    ctx: RequestContext = Depends(TokenVerifier),
) -> List[TaskModel]:
    return read_user(user_id=ctx.user_id, offset=offset, limit=limit)
