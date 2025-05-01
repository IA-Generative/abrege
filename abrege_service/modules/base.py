from typing import List, Optional
from abc import ABC, abstractmethod
import time
from src.schemas.task import TaskModel, task_table, TaskStatus, TaskUpdateForm
from src.schemas.result import ResultModel
from src.schemas.content import DocumentModel


class NoGivenInput(Exception): ...


class BaseService(ABC):
    def __init__(self, content_type_allowed: List[str] = []):
        self.task_table = task_table
        self.content_type_allowed = content_type_allowed

    def is_availble(self, content_type: str) -> bool:
        return content_type in self.content_type_allowed

    def update_task(
        self,
        task: TaskModel,
        result: Optional[ResultModel] = None,
        status: Optional[TaskStatus] = None,
    ) -> TaskModel:
        return self.task_table.update_task(
            task_id=task.id,
            form_data=TaskUpdateForm(
                status=status,
                result=result,
                updated_at=int(time.time()),
                extras=task.extras,
            ),
        )

    @abstractmethod
    def task_to_text(self, task: TaskModel, **kwargs) -> TaskModel: ...

    def process_task(self, task: TaskModel, **kwargs):
        if task.content is None:
            raise NoGivenInput("No input is given")

        if isinstance(task.content, DocumentModel):
            content_type: str = task.content.content_type
            if not self.is_availble(content_type):
                raise NotImplementedError(f"Content type {content_type} is not available for processing.")
        return self.task_to_text(task, **kwargs)
