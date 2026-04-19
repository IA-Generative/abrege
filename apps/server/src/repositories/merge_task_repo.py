from src.schemas.merge_task import MergeTask as MergeTaskSchema
from src.models.merge_task import MergeTask
from src.internal.db import get_db


class MergeTaskTable:
    def create_merge_task(self, merge_task: MergeTaskSchema) -> MergeTask:
        with get_db() as db:
            db.add(merge_task)
            db.commit()
            db.refresh(merge_task)
            return MergeTask.model_validate(merge_task)

    def get_merge_tasks_by_merge_id(self, merge_id: str) -> list[MergeTask]:
        with get_db() as db:
            rows = db.query(MergeTaskSchema).filter(MergeTaskSchema.merge_id == merge_id).all()
            return [MergeTask.model_validate(r) for r in rows]

    def update_merge_task(self, task_id: str, **kwargs) -> MergeTask | None:
        with get_db() as db:
            task = db.query(MergeTaskSchema).filter(MergeTaskSchema.id == task_id).first()
            if not task:
                return None
            for key, value in kwargs.items():
                setattr(task, key, value)
            db.commit()
            db.refresh(task)
            return MergeTask.model_validate(task)

    def delete_merge_tasks_by_merge_id(self, merge_id: str) -> None:
        with get_db() as db:
            tasks = db.query(MergeTaskSchema).filter(MergeTaskSchema.merge_id == merge_id).all()
            for task in tasks:
                db.delete(task)
            db.commit()

    def get_by_related_task_id(self, task_id: str) -> MergeTask | None:
        with get_db() as db:
            row = db.query(MergeTaskSchema).filter(MergeTaskSchema.related_task == task_id).first()
            return MergeTask.model_validate(row) if row else None

    def count_merge_tasks_by_merge_id(self, merge_id: str) -> int:
        with get_db() as db:
            return db.query(MergeTaskSchema).filter(MergeTaskSchema.merge_id == merge_id).count()

    def is_merge_completed(self, merge_id: str) -> bool:
        with get_db() as db:
            return (
                db.query(MergeTaskSchema)
                .filter(
                    MergeTaskSchema.merge_id == merge_id,
                    MergeTaskSchema.status != "completed",
                )
                .count()
                == 0
            )
