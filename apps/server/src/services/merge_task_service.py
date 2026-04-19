from src.repositories.merge_task_repo import MergeTaskTable
from src.models.merge_task import MergeTask, MergeTaskCreateForm, MergeTaskUpdateForm
from src.schemas.merge_task import MergeTask as MergeTaskSchema
import time


class MergeTaskService:
    def __init__(self):
        self.merge_task_repo = MergeTaskTable()

    def create_merge_task(self, merge_task_create: MergeTaskCreateForm) -> MergeTask:
        now = int(time.time())
        schema = MergeTaskSchema(
            **merge_task_create.model_dump(),
            created_at=now,
            updated_at=now,
        )
        return self.merge_task_repo.create_merge_task(schema)

    def get_merge_task_by_merge_id(self, merge_id: str) -> list[MergeTask]:
        return self.merge_task_repo.get_merge_tasks_by_merge_id(merge_id)

    def update_merge_task(self, task_id: str, merge_task_update: MergeTaskUpdateForm) -> MergeTask | None:
        return self.merge_task_repo.update_merge_task(task_id, **merge_task_update.model_dump())

    def delete_merge_tasks_by_merge_id(self, merge_id: str):
        self.merge_task_repo.delete_merge_tasks_by_merge_id(merge_id)

    def count_merge_tasks_by_merge_id(self, merge_id: str) -> int:
        return self.merge_task_repo.count_merge_tasks_by_merge_id(merge_id)

    def is_merge_completed(self, merge_id: str) -> bool:
        return self.merge_task_repo.is_merge_completed(merge_id)

    def get_by_related_task_id(self, task_id: str) -> MergeTask | None:
        return self.merge_task_repo.get_by_related_task_id(task_id)


merge_task_service = MergeTaskService()
