import json
import os
import traceback
from typing import Optional
from datetime import datetime
from typing import Annotated
import aiofiles
from fastapi import (
    File,
    UploadFile,
    HTTPException,
    status as http_status,
    Form,
    APIRouter,
    Depends,
)
from src.clients import file_connector, celery_app
from src.utils.logger import logger_abrege as logger

from src.models.task import (
    TaskForm,
    TaskUpdateForm,
    TaskStatus,
    TaskModel,
    TaskName,
)
from src.schemas.content import DocumentModel
from api.schemas.content import Content
from src.schemas.parameters import SummaryParameters
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

doc_router = APIRouter(tags=["Document"])
TokenDep = Annotated[RequestContext, Depends(TokenVerifier)]
DbDep = Annotated[AsyncSession, Depends(get_async_session_dep)]
TaskServiceDep = Annotated[TaskService, Depends(TaskService)]


async def summarize_doc(
    db: DbDep,
    service: TaskServiceDep,
    file: UploadFile = File(...),
    user_id: str = Form(..., description="User id"),
    prompt: Optional[str] = Form(None, description="Custom prompt for after summary"),
    parameters: Optional[str] = Form(
        default="",
        description=f"Parameters {SummaryParameters().model_dump()}",
    ),
):
    extras = {}

    if parameters is not None and parameters:
        try:
            parameters: SummaryParameters = SummaryParameters.model_validate_json(
                parameters
            )
        except Exception as e:
            raise HTTPException(
                status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"{e}"
            )
    else:
        parameters: SummaryParameters = SummaryParameters()

    if llm_guard is not None and parameters.custom_prompt is not None:
        try:
            parameters.custom_prompt = llm_guard.request_llm_guard_prompt(
                prompt=parameters.custom_prompt
            )
        except LLMGuardRequestException:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=" Bad request for the guard",
            )
        except LLMGuardMaliciousPromptException:
            raise HTTPException(
                status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Unprocessable Entity (Suspicious)",
            )

    content = Content(prompt=prompt, extras=extras)

    task_data = await service.insert_new_task(
        db=db,
        user_id=user_id,
        form_data=TaskForm(
            type="summary",
            status=TaskStatus.CREATED.value,
            parameters=parameters,
            extras=extras,
        ),
    )

    try:
        async with aiofiles.tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file_path = temp_file.name

            # Lecture par chunks pour économiser la mémoire
            chunk_size = 8192  # 8KB chunks
            while chunk := await file.read(chunk_size):
                await temp_file.write(chunk)

        logger.debug(task_data.model_dump())

        saved_path = file_connector.save(user_id, task_data.id, temp_file_path)
        logger.debug(
            f"Save into S3 - {saved_path}",
            extra={"task_id": task_data.id, "user_id": task_data.user_id},
        )

        _, extension = os.path.splitext(file.filename)

        extras = task_data.extras  # ty:ignore[invalid-assignment]

        document_content = DocumentModel(
            created_at=int(datetime.now().timestamp()),
            file_path=saved_path,
            raw_filename=os.path.basename(file.filename),
            content_type=file.content_type,
            ext=extension,
            size=file.size,
            extras=content.extras if content else {},
        )

        task_data = await service.update_task(
            db=db,
            task_id=task_data.id,
            form_data=TaskUpdateForm(
                status=TaskStatus.QUEUED.value,
                input=document_content,
                extras=extras,
            ),
        )
        if task_data is None:
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update task with document content",
            )

        os.remove(temp_file_path)

        celery_app.send_task(
            name=TaskName.ABREGE.value,
            args=[json.dumps(task_data.model_dump())],
            task_id=task_data.id,
            retries=2,
        )

        return task_data

    except Exception as e:
        logger.error(
            f"Failed to upload file for user {user_id}, task {task_data}: {e} - {traceback.format_exc()}"
        )
        await service.update_task(
            db=db,
            task_id=task_data.id,  # ty:ignore[unresolved-attribute]
            form_data=TaskUpdateForm(
                status=TaskStatus.FAILED.value,
                extras={"error": str(e)},
            ),
        )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="File upload failed",
        )


@doc_router.post(
    "/task/document", status_code=http_status.HTTP_201_CREATED, response_model=TaskModel
)
async def new_summarize_doc(
    ctx: TokenDep,
    db: DbDep,
    service: TaskServiceDep,
    file: UploadFile = File(...),
    prompt: Annotated[
        Optional[str], Form(description="Custom prompt for after summary")
    ] = None,
    parameters: Annotated[
        Optional[str],
        Form(
            description=f"Parameters {SummaryParameters().model_dump()}",
        ),
    ] = "",
):
    if ctx.user_id is None:
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
        )
    return await summarize_doc(
        file=file,
        user_id=ctx.user_id,
        prompt=prompt,
        parameters=parameters,
        db=db,
        service=service,
    )
