from typing import List
from fastapi import APIRouter, HTTPException

from src.schemas.task import task_table, TaskModel
from src.utils.logger import logger_abrege

router = APIRouter(tags=["Tasks"])


@router.get("/task/{id}", response_model=TaskModel)
async def read(id: str) -> TaskModel:
    task = task_table.get_task_by_id(task_id=id)
    if task is None:
        raise HTTPException(404, detail=f"{id} not found")
    return task


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
