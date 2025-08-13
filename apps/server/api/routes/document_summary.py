import aiofiles
import json
import os
import traceback
from typing import Optional
from datetime import datetime
from fastapi import (
    File,
    UploadFile,
    HTTPException,
    status,
    Form,
    APIRouter,
    Depends,
    Request,
)
from src.clients import file_connector, celery_app
from src.utils.logger import logger_abrege as logger
from src.schemas.task import task_table, TaskForm, TaskUpdateForm, TaskStatus, TaskModel
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

doc_router = APIRouter(tags=["Document"])


async def summarize_doc(
    file: UploadFile = File(...),
    user_id: str = Form(..., description="User id"),
    prompt: Optional[str] = Form(None, description="Custom prompt for after summary"),
    parameters: Optional[str] = Form(
        default="",
        description=f"Parameters {SummaryParameters().model_dump()}",
    ),
    extras: Optional[str] = Form(default="", description="Extras json payload"),
    headers: Optional[dict] = Form(default=None, description="Request headers"),
):
    if extras is not None and extras:
        try:
            extras = json.loads(extras)
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"{e}")
    else:
        extras = {}

    if parameters is not None and parameters:
        try:
            parameters: SummaryParameters = SummaryParameters.model_validate_json(parameters)
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"{e}")
    else:
        parameters: SummaryParameters = SummaryParameters()

    parameters.headers = headers if headers is not None else {}
    if llm_guard is not None and parameters.custom_prompt is not None:
        try:
            parameters.custom_prompt = llm_guard.request_llm_guard_prompt(prompt=parameters.custom_prompt)
        except LLMGuardRequestException:
            raise HTTPException(status_code=400, detail=" Bad request for the guard")
        except LLMGuardMaliciousPromptException:
            raise HTTPException(status_code=422, detail="Unprocessable Entity (Suspicious)")

    content = Content(prompt=prompt, extras=extras)

    task_data = task_table.insert_new_task(
        user_id=user_id,
        form_data=TaskForm(
            user_id=user_id,
            type="summary",
            status=TaskStatus.CREATED.value,
            parameters=parameters,
            extras=extras,
        ),
    )
    try:
        async with aiofiles.tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file_path = temp_file.name
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

        extras = task_data.extras

        document_content = DocumentModel(
            created_at=int(datetime.now().timestamp()),
            file_path=saved_path,
            raw_filename=os.path.basename(file.filename),
            content_type=file.content_type,
            ext=extension,
            size=file.size,
            extras=content.extras if content else {},
        )

        task_data = task_table.update_task(
            task_id=task_data.id,
            form_data=TaskUpdateForm(
                status=TaskStatus.QUEUED.value,
                input=document_content,
                extras=extras,
            ),
        )

        os.remove(temp_file_path)

        celery_app.send_task(
            "worker.tasks.abrege",
            args=[json.dumps(task_data.model_dump())],
            task_id=task_data.id,
            retries=2,
        )

        return task_data

    except Exception as e:
        logger.error(f"Failed to upload file for user {user_id}, task {task_data.id}: {e} - {traceback.format_exc()}")
        task_table.update_task(
            task_id=task_data.id,
            form_data=TaskUpdateForm(
                status=TaskStatus.FAILED.value,
                extras={"error": str(e)},
            ),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="File upload failed",
        )


@doc_router.post("/task/document", status_code=status.HTTP_201_CREATED, response_model=TaskModel)
async def new_summarize_doc(
    request: Request,
    file: UploadFile = File(...),
    prompt: Optional[str] = Form(None, description="Custom prompt for after summary"),
    parameters: Optional[str] = Form(
        default="",
        description=f"Parameters {SummaryParameters().model_dump()}",
    ),
    extras: Optional[str] = Form(default="", description="Extras json payload"),
    ctx: RequestContext = Depends(TokenVerifier),
):
    # Récupérer les headers et les convertir en dictionnaire
    # Récupérer seulement le header authorization
    headers = {}
    if "authorization" in request.headers:
        headers["authorization"] = request.headers["authorization"]

    return await summarize_doc(
        file=file,
        user_id=ctx.user_id,
        prompt=prompt,
        parameters=parameters,
        extras=extras,
        headers=headers,  # Pass headers to the function
    )
