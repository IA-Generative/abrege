from sqlalchemy.ext.asyncio import AsyncSession
from src.schemas.task import (
    TaskForm,
    TaskModel,
    TaskUpdateForm,
    TaskStats,
)

from src.repositories.task_repo import TaskRepository


class TaskService:
    def __init__(self):
        self.task_repo = TaskRepository()

    async def health_check(self, db: AsyncSession) -> tuple[bool, str | None]:
        return await self.task_repo.health_check(db)

    async def insert_new_task(self, db: AsyncSession, user_id: str, form_data: TaskForm) -> TaskModel:
        return await self.task_repo.insert_new_task(db, user_id, form_data)

    async def get_task_by_id(self, db: AsyncSession, task_id: str) -> TaskModel | None:
        return await self.task_repo.get_task_by_id(db, task_id)

    async def update_task(self, db: AsyncSession, task_id: str, form_data: TaskUpdateForm) -> TaskModel | None:
        return await self.task_repo.update_task(db, task_id, form_data)

    async def delete_task_by_id(self, db: AsyncSession, task_id: str) -> None:
        await self.task_repo.delete_task_by_id(db, task_id)

    async def get_position_in_queue(self, db: AsyncSession, task_id: str) -> int | None:
        return await self.task_repo.get_position_in_queue(db, task_id)

    async def get_statistics(
        self,
        db: AsyncSession,
        user_id: str,
        is_admin: bool,
        skip: int,
        limit: int,
        start_date: int | None = None,
        end_date: int | None = None,
    ) -> TaskStats:
        return await self.task_repo.statistics(
            db=db,
            user_id=user_id,
            is_admin=is_admin,
            skip=skip,
            limit=limit,
            start_date=start_date,
            end_date=end_date,
        )

    async def get_tasks_by_user_id(self, db: AsyncSession, user_id: str, page: int, page_size: int) -> list[TaskModel]:
        return await self.task_repo.get_tasks_by_user_id(db=db, user_id=user_id, page=page, page_size=page_size)

    async def count_tasks_by_user_id(self, db: AsyncSession, user_id: str) -> int:
        return await self.task_repo.count_tasks_by_user_id(db=db, user_id=user_id)

    async def delete_tasks_by_user_id(self, db: AsyncSession, user_id: str) -> None:
        await self.task_repo.delete_tasks_by_user_id(db=db, user_id=user_id)

    async def get_tasks_by_ids(self, db: AsyncSession, user_id: str, task_ids: list[str]) -> list[TaskModel]:
        return await self.task_repo.get_tasks(db=db, user_id=user_id, task_ids=task_ids)

    async def count_unique_users_between_dates(self, db: AsyncSession, start_date: int, end_date: int) -> int:
        return await self.task_repo.count_unique_users_between_dates(db=db, start_date=start_date, end_date=end_date)

    async def search_task_by_fields(self, db: AsyncSession, **filters) -> TaskModel | None:
        return await self.task_repo.search_task_by_fields(db=db, **filters)
