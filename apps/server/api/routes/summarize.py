import json
from datetime import datetime

from fastapi import APIRouter, status, HTTPException, Depends

from api.schemas.content import UrlContent, TextContent

from api.utils.url import is_valid_url

from src.clients import celery_app
from src.schemas.content import URLModel, TextModel
from src.schemas.task import task_table, TaskModel, TaskForm, TaskStatus
from src.utils.logger import logger_abrege as logger
from api.schemas.content import InputModel, Input
from api.clients.llm_guard import (
    llm_guard,
    LLMGuardMaliciousPromptException,
    LLMGuardRequestException,
)
from api.core.security.token import RequestContext
from api.core.security.factory import TokenVerifier
from api.docs import USER_SECURITY, UNAUTHORIZED, ErrorResponse

router = APIRouter(tags=["Text & Url"])


def summarize_content(input: InputModel):
    content = input.content
    parameters = input.parameters
    if llm_guard is not None and parameters and parameters.custom_prompt is not None:
        try:
            parameters.custom_prompt = llm_guard.request_llm_guard_prompt(prompt=parameters.custom_prompt)
        except LLMGuardRequestException:
            raise HTTPException(status_code=400, detail=" Bad request for the guard")
        except LLMGuardMaliciousPromptException:
            raise HTTPException(status_code=422, detail="Unprocessable Entity (Suspicious)")

    if isinstance(content, UrlContent):
        model_to_send = URLModel(
            created_at=int(datetime.now().timestamp()),
            extras=content.extras,
            url=content.url,
        )
        if not is_valid_url(model_to_send.url):
            raise HTTPException(status_code=422, detail=f"{model_to_send.url} is not a valid URL")

    elif isinstance(content, TextContent):
        model_to_send = TextModel(
            created_at=int(datetime.now().timestamp()),
            extras=content.extras,
            text=content.text,
        )
    else:
        raise HTTPException(status_code=422, detail=f" {content} is not available")

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
    logger.debug({"task_id": task.id, "user_id": task.user_id, "time": task.created_at})
    celery_app.send_task(
        "worker.tasks.abrege",
        args=[json.dumps(task.model_dump())],
        retries=2,
        task_id=task.id,
    )

    return task


@router.post(
    "/task/text-url",
    status_code=status.HTTP_201_CREATED,
    response_model=TaskModel,
    summary="Summarize a text or a URL",
    description="""Create a summarization task from a text or from a URL and queue it. The task is returned right away in `created`
state: poll `GET /api/task/{id}` until it is `completed`.

The body is JSON: `content` holds either `{"text": "..."}` or `{"url": "..."}`, and `parameters` the summary
options (language, size, optional Q&A / entities / chunks / topics extractions, with their instructions and definitions).
For a file, use `POST /api/task/document` instead.""",
    responses={
        400: {"model": ErrorResponse, "description": "The prompt was rejected by the guard (bad request)."},
        422: {"model": ErrorResponse, "description": "Invalid body, unsupported content, or suspicious prompt."},
        **UNAUTHORIZED,
    },
    openapi_extra={"security": USER_SECURITY},
)
async def new_summarize_content(
    input: Input,
    ctx: RequestContext = Depends(TokenVerifier),
):
    input_model = InputModel(user_id=ctx.user_id, **input.model_dump())

    return summarize_content(input=input_model)
