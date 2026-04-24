from src.models.task import TaskUpdateForm, TaskName
from src.clients import celery_app
from src.utils.logger import logger_abrege

from abrege_service.clients.server import ServerClient

import time

server_client = ServerClient()


@celery_app.task(name=TaskName.UPDATE_TASK.value, bind=True)
def updating_task(self, task_id: str, update_form: str | dict) -> dict:
    with logger_abrege.contextualize(  # ty:ignore[unresolved-attribute]
        task_id=task_id, action=TaskName.UPDATE_TASK.value
    ):
        if isinstance(update_form, str):
            update_data = TaskUpdateForm.model_validate_json(update_form)
        else:
            update_data = TaskUpdateForm.model_validate(update_form)
        update_data.updated_at = int(time.time())
        return server_client.update_task(
            task_id=task_id,
            data=update_data.model_dump(exclude_none=True),
        )
