from typing import List, Optional
from abc import ABC, abstractmethod
import time
from src.models.task import TaskModel, TaskStatus, TaskUpdateForm
from src.schemas.result import ResultModel
from src.schemas.content import DocumentModel, URLModel, ContentModel
from abrege_service.clients.server import ServerClient
from loguru import logger
import sys

logger.remove()
logger.add(sys.stdout, level="DEBUG")

client = ServerClient()


class NoGivenInput(Exception): ...


class BaseService(ABC):
    def __init__(self, content_type_allowed: List[str] = [], service_weight: float = 0.5):
        self.content_type_allowed = content_type_allowed
        self.service_weight = service_weight

    def is_available(self, task: TaskModel) -> bool:
        return task.input.content_type in self.content_type_allowed

    def update_task(
        self,
        task: TaskModel,
        result: Optional[ResultModel] = None,
        status: Optional[TaskStatus] = None,
        input: Optional[DocumentModel | URLModel | ContentModel] = None,
    ) -> TaskModel:
        percentage = None
        if result is not None:
            percentage = result.percentage * self.service_weight

        task_data = client.update_task(
            task_id=task.id,
            data=TaskUpdateForm(
                status=status,
                output=result,
                updated_at=int(time.time()),
                extras=task.extras,
                percentage=percentage,
                content_hash=task.content_hash,
            ).model_dump(exclude_none=True),
        )
        logger.debug(f"Task {task.id} updated with status {status} and percentage {percentage}")

        return TaskModel.model_validate(task_data)

    @abstractmethod
    def task_to_text(self, task: TaskModel, **kwargs) -> TaskModel: ...

    def process_task(self, task: TaskModel, **kwargs):
        if task.input is None:
            raise NoGivenInput("No input is given")

        if isinstance(task.input, DocumentModel):
            content_type: str = task.input.content_type
            if not self.is_available(task=task):
                raise NotImplementedError(f"Content type {content_type} is not available for processing.")
        return self.task_to_text(task, **kwargs)
