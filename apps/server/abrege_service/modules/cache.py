from abrege_service.modules.base import BaseService
from src.schemas.task import TaskModel, TaskStatus


from src.utils.logger import logger_abrege


class CacheService(BaseService):
    def __init__(self, content_type_allowed=..., service_weight=0.5):
        super().__init__(content_type_allowed, service_weight)

    def is_available(self, task: TaskModel) -> bool:
        if task.content_hash:
            logger_abrege.debug(f"[task_id {task.id}] Checking cache for task with content_hash: {task.content_hash}")
            if self.task_table.search_task_by_fields(content_hash=task.content_hash, status=TaskStatus.COMPLETED.value):
                logger_abrege.debug(f"[task_id {task.id}] Task found in cache with content_hash: {task.content_hash}")
                return True
        return False

    def task_to_text(self, task: TaskModel, **kwargs) -> TaskModel:
        task_found = self.task_table.search_task_by_fields(content_hash=task.content_hash, status=TaskStatus.COMPLETED.value)

        if task_found:
            task.output = task_found.output
            task.percentage = task_found.percentage * self.service_weight
            return task

        raise NotImplementedError(f"Task with content_hash {task.content_hash} not found.")
