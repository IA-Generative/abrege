from typing import Optional
from abc import ABC, abstractmethod
import time
from src.schemas.task import TaskModel, TaskStatus, task_table, TaskUpdateForm
from src.schemas.result import SummaryModel


class TextResultNotGiven(Exception): ...


class BaseSummaryService(ABC):
    def update_result_task(
        self, task: TaskModel, result: Optional[SummaryModel] = None, status: Optional[TaskStatus] = None, percentage: Optional[float] = 0.0
    ) -> TaskModel:
        return task_table.update_task(
            task_id=task.id,
            form_data=TaskUpdateForm(status=status, output=result, updated_at=int(time.time()), extras=task.extras, percentage=percentage),
        )

    @abstractmethod
    def summarize(self, task: TaskModel, *args, **kwargs) -> TaskModel: ...

    def process_task(self, task: TaskModel, *args, **kwargs) -> TaskModel:
        if task.output is None or not task.output.texts_found:
            raise TextResultNotGiven("No text is given")

        return self.summarize(task=task)
