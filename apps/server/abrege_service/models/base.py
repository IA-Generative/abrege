from typing import Optional
from abc import ABC, abstractmethod
import time
from src.models.task import TaskModel, TaskStatus, TaskUpdateForm
from src.schemas.result import SummaryModel
from abrege_service.clients.server import ServerClient

server_client = ServerClient()


class TextResultNotGiven(Exception): ...


class BaseSummaryService(ABC):
    def update_result_task(
        self,
        task: TaskModel,
        result: Optional[SummaryModel] = None,
        status: Optional[TaskStatus] = None,
        percentage: Optional[float] = 0.0,
    ) -> TaskModel:
        task_data = server_client.update_task(
            task_id=task.id,
            data=TaskUpdateForm(
                status=status,
                output=result,
                updated_at=int(time.time()),
                extras=task.extras,
                percentage=percentage,
            ).model_dump(exclude_none=True),
        )
        return TaskModel.model_validate(task_data)

    @abstractmethod
    def summarize(self, task: TaskModel, *args, **kwargs) -> TaskModel: ...

    def process_task(self, task: TaskModel, *args, **kwargs) -> TaskModel:
        if task.output is None or not task.output.texts_found:
            raise TextResultNotGiven("No text is given")

        return self.summarize(task=task)
