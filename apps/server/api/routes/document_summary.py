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
import tempfile
import shutil

doc_router = APIRouter(tags=["Document"])

MAX_FILE_SIZE = 200 * 1024 * 1024
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "text/plain",
    "application/vnd.oasis.opendocument.text",
    "application/vnd.oasis.opendocument.presentation",
}


async def summarize_doc(
    file: UploadFile = File(...),
    user_id: str = Form(..., description="User id"),
    prompt: Optional[str] = Form(None, description="Custom prompt for after summary"),
    parameters: Optional[str] = Form(
        default="",
        description=f"Parameters {SummaryParameters().model_dump()}",
    ),
    extras: Optional[str] = Form(default="", description="Extras json payload"),
):
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    if size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File exceeds the maximum allowed size",
        )
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported file type",
        )
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
    temp_file_path: Optional[str] = None
    try:
        # Créer un fichier temporaire
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file_path = temp_file.name

            # Copier directement le contenu du fichier uploadé
            file.file.seek(0)  # S'assurer qu'on est au début du fichier
            shutil.copyfileobj(file.file, temp_file)

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
            size=size,
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
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        logger.error(
            f"Failed to upload file for user {user_id}, task {task_data.id}: {e} - {traceback.format_exc()}"
        )
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
    file: UploadFile = File(...),
    prompt: Optional[str] = Form(None, description="Custom prompt for after summary"),
    parameters: Optional[str] = Form(
        default="",
        description=f"Parameters {SummaryParameters().model_dump()}",
    ),
    extras: Optional[str] = Form(default="", description="Extras json payload"),
    ctx: RequestContext = Depends(TokenVerifier),
):
    return await summarize_doc(
        file=file,
        user_id=ctx.user_id,
        prompt=prompt,
        parameters=parameters,
        extras=extras,
    )
