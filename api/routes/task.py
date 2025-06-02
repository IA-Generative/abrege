from typing import List
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from src.schemas.task import task_table, TaskModel
from src.schemas.code_error import TASK_STATUS_TO_HTTP
from src.utils.logger import logger_abrege


router = APIRouter(tags=["Tasks"])


@router.get("/task/{id}", response_model=TaskModel)
async def read(id: str) -> TaskModel:
    task = task_table.get_task_by_id(task_id=id)
    if task is None:
        raise HTTPException(404, detail=f"{id} not found")

    task.position = task_table.get_position_in_queue(task_id=id)
    return JSONResponse(task.model_dump(), status_code=TASK_STATUS_TO_HTTP.get(task.status, 200))


@router.get("/task/user/{user_id}", response_model=List[TaskModel])
async def read_user(user_id: str, offset: int = 1, limit: int = 10) -> List[TaskModel]:
    try:
        tasks = task_table.get_tasks_by_user_id(user_id=user_id, page=offset, page_size=limit)
        if tasks is None:
            raise HTTPException(404, detail=f"{id} not found")
    except Exception as e:
        logger_abrege.error(e)
        raise HTTPException(500, detail=f"{str(e)} not found")

    return tasks
