import json
from datetime import datetime

from fastapi import APIRouter, status, HTTPException, Depends
from fastapi.responses import JSONResponse

from api.schemas.content import UrlContent, TextContent

from api.utils.url import check_url, get_status_code_and_code

from src.clients import celery_app
from src.schemas.content import URLModel, TextModel
from src.schemas.task import TaskModel, TaskForm, TaskStatus
from src.utils.logger import logger_abrege as logger
from api.schemas.content import InputModel, Input
from api.clients.llm_guard import (
    llm_guard,
    LLMGuardMaliciousPromptException,
    LLMGuardRequestException,
)
from api.core.security.token import RequestContext
from api.core.security.factory import TokenVerifier


from src.internal.db import get_async_session_dep
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.task_service import TaskService
from typing import Annotated


router = APIRouter(tags=["Tasks"])

TokenDep = Annotated[RequestContext, Depends(TokenVerifier)]
DbDep = Annotated[AsyncSession, Depends(get_async_session_dep)]
TaskServiceDep = Annotated[TaskService, Depends(TaskService)]


async def summarize_content(
    input: InputModel,
    service: TaskServiceDep,
    db: DbDep,
) -> TaskModel:
    content = input.content
    parameters = input.parameters
    if llm_guard is not None and parameters and parameters.custom_prompt is not None:
        try:
            parameters.custom_prompt = llm_guard.request_llm_guard_prompt(prompt=parameters.custom_prompt)
        except LLMGuardRequestException:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=" Bad request for the guard",
            )
        except LLMGuardMaliciousPromptException:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Unprocessable Entity (Suspicious)",
            )

    if isinstance(content, UrlContent):
        model_to_send = URLModel(
            created_at=int(datetime.now().timestamp()),
            extras=content.extras,
            url=content.url,
        )
        if not check_url(url=model_to_send.url):
            status_code, error_content = get_status_code_and_code(url=model_to_send.url)
            return JSONResponse(
                status_code=status_code,
                content={"msg": f"L'url {model_to_send.url} n'est pas accessible par le systeme detail : {error_content}"},
            )

    elif isinstance(content, TextContent):
        model_to_send = TextModel(
            created_at=int(datetime.now().timestamp()),
            extras=content.extras,
            text=content.text,
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f" {content} is not available",
        )

    model_to_send.extras = model_to_send.extras if model_to_send.extras is not None else {}
    model_to_send.extras["prompt"] = content.prompt

    task = await service.insert_new_task(
        db=db,
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
)
async def new_summarize_content(
    input: Input,
    ctx: TokenDep,
):
    if ctx.user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    input_model = InputModel(user_id=ctx.user_id, **input.model_dump())

    return await summarize_content(input=input_model, service=TaskService(), db=AsyncSession())
