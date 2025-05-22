import json
from datetime import datetime

from fastapi import APIRouter, status, HTTPException

from api.schemas.content import UrlContent, TextContent

from api.utils.url import check_url

from src.clients import celery_app
from src.schemas.content import URLModel, TextModel
from src.schemas.task import task_table, TaskModel, TaskForm, TaskStatus
from src.logger.logger import logger
from api.schemas.content import InputModel

router = APIRouter(tags=["Text & Url"])


@router.post(
    "/task/text-url",
    status_code=status.HTTP_201_CREATED,
    response_model=TaskModel,
)
async def summarize_content(input: InputModel):
    content = input.content
    parameters = input.parameters
    if isinstance(content, UrlContent):
        model_to_send = URLModel(
            created_at=int(datetime.now().timestamp()),
            extras=content.extras,
            url=content.url,
        )
        if not check_url(url=model_to_send.url):
            raise HTTPException(status_code=500, detail=f"url {model_to_send.url} is not valid")

    elif isinstance(content, TextContent):
        model_to_send = TextModel(
            created_at=int(datetime.now().timestamp()),
            extras=content.extras,
            text=content.text,
        )
    else:
        raise HTTPException(status_code=500, detail=f" {content} is not available")

    model_to_send.extras = model_to_send.extras if model_to_send.extras is not None else {}
    model_to_send.extras["prompt"] = content.prompt

    task = task_table.insert_new_task(
        user_id=input.user_id,
        form_data=TaskForm(
            type="summary",
            status=TaskStatus.CREATED.value,
            input=model_to_send,
            parameters=parameters,
        ),
    )
    logger.debug({"task_id": task.id, "time": task.created_at})
    celery_app.send_task(
        "worker.tasks.abrege",
        args=[json.dumps(task.model_dump())],
        retries=2,
        task_id=task.id,
    )

    return task
