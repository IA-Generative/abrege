import json
import traceback


from src.models.task import TaskModel, TaskStatus
from celery import Task
from src.utils.logger import logger_abrege
from src.services.merge_task_service import merge_task_service
from src.models.merge_task import MergeTaskUpdateForm
from .merge import launch_merge
from .chunk_task import launch_chunking
from .tools import server_client


class AbregeTask(Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger_abrege.error(f"Task {task_id} failed: {exc} - {traceback.format_exc()}")
        task = merge_task_service.get_by_related_task_id(task_id=task_id)
        if task:
            merge_task_service.update_merge_task(
                task_id=task.id,
                merge_task_update=MergeTaskUpdateForm(
                    status=TaskStatus.FAILED.value,
                ),
            )

    def on_success(self, retval, task_id, args, kwargs):
        logger_abrege.info(f"Task {task_id} completed successfully")
        task_id_process = retval.get("id") if isinstance(retval, dict) else None
        if not task_id_process:
            logger_abrege.warning(f"Task {task_id} did not return a valid task id in retval: {retval}")
            return
        current_task = server_client.get_task(task_id=task_id_process)
        launch_chunking.apply_async(
            args=[json.dumps(current_task)],
            task_id=f"{task_id}-chunking",
        )
        task = merge_task_service.get_by_related_task_id(task_id=task_id_process)
        if task:
            merge_task_service.update_merge_task(
                task_id=task.id,
                merge_task_update=MergeTaskUpdateForm(
                    status=TaskStatus.COMPLETED.value,
                    percentage=1,
                ),
            )
            task = merge_task_service.get_by_related_task_id(task_id=task_id_process)
            if task and merge_task_service.is_merge_completed(merge_id=task.merge_id):
                logger_abrege.info(f"All tasks for merge {task.merge_id} are completed. Marking merge as completed.")
                merge_task_model = server_client.get_task(task_id=task.merge_id)
                merge_task_model = TaskModel.model_validate(merge_task_model)
                launch_merge.apply_async(
                    args=[json.dumps(merge_task_model.model_dump())],
                    task_id=task.merge_id,
                )
