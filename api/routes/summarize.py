from typing import Union
from fastapi import APIRouter, status
from api.schemas.content import UrlContent, TextContent
from src.schemas.content import URLModel, TextModel
from src.schemas.task import task_table, TaskModel, TaskForm
from datetime import datetime

router = APIRouter(tags=["Text"])


@router.post("/content/{user_id}", status_code=status.HTTP_201_CREATED, response_model=TaskModel)
async def summarize_content(user_id: str, content: Union[UrlContent, TextContent]):
    if isinstance(content, UrlContent):
        model_to_send = URLModel(created_at=int(datetime.now().timestamp()), extras=content.extras, url=content.url)

    if isinstance(content, TextModel):
        model_to_send = URLModel(created_at=int(datetime.now().timestamp()), extras=content.extras, text=content.text)

    model_to_send.extras = model_to_send.extras if model_to_send.extras is not None else {}
    model_to_send.extras["prompt"] = content.prompt

    task = task_table.insert_new_task(user_id=user_id, form_data=TaskForm(type="summary", status=None, content=model_to_send))

    return task
