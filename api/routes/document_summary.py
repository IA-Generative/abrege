import json
import tempfile
import shutil
import os
import traceback
from datetime import datetime
from fastapi import APIRouter, File, UploadFile, HTTPException, status, Form
from pydantic import ValidationError

from api.schemas.content import Content
from api.utils.content_type import get_content_type

from src.clients import file_connector, celery_app
from src.logger.logger import logger
from src.schemas.task import (
    task_table,
    TaskForm,
    TaskModel,
    TaskUpdateForm,
    TaskStatus,
)
from src.schemas.content import DocumentModel

router = APIRouter(tags=["Document"])


@router.post("/doc/{user_id}", status_code=status.HTTP_201_CREATED, response_model=TaskModel)
async def summarize_doc(
    user_id: str,
    content: str = Form(...),
    file: UploadFile = File(...),
):
    try:
        content: Content = Content.model_validate_json(content)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors())

    extras = {}
    task_data = task_table.insert_new_task(
        user_id=user_id,
        form_data=TaskForm(
            user_id=user_id,
            type="summary",
            status=TaskStatus.CREATED.value,
            extras=extras,
        ),
    )
    try:
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file_path = temp_file.name  # Le chemin du fichier temporaire
            with open(temp_file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

        logger.debug(task_data.model_dump())

        saved_path = file_connector.save(user_id, task_data.id, temp_file_path)
        logger.debug(f"Save into S3 - {saved_path}")

        _, extension = os.path.splitext(file.filename)

        extras = task_data.extras

        document_content = DocumentModel(
            created_at=int(datetime.now().timestamp()),
            file_path=saved_path,
            prompt=content.prompt,
            raw_filename=os.path.basename(file.filename),
            content_type=get_content_type(file),
            ext=extension,
            size=file.size,
            extras=content.extras,
        )

        task_data = task_table.update_task(
            task_id=task_data.id,
            form_data=TaskUpdateForm(
                status=TaskStatus.QUEUED.value,
                content=document_content,
                extras=extras,
            ),
        )

        os.remove(temp_file_path)

        celery_app.send_task(
            "worker.tasks.ocr",
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
