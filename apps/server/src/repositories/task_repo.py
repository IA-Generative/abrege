import uuid
import time
from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas.pagination import Pagination
from src.utils.logger import logger_abrege as logger
from src.models.task import (
    TaskModel,
    TaskForm,
    TaskUpdateForm,
    TaskStatus,
    TaskStatsGlobal,
    TaskStatsUser,
    TaskStats,
)
from src.schemas.task import Task


class TaskRepository:
    async def health_check(self, db: AsyncSession) -> tuple[bool, Optional[str]]:
        try:
            await db.execute(select(Task).limit(1))
            return True, None
        except SQLAlchemyError as e:
            return False, str(e)

    async def insert_new_task(self, db: AsyncSession, user_id: str, form_data: TaskForm) -> TaskModel:
        # Nettoyer les parameters pour enlever le token
        result = Task(
            id=str(uuid.uuid4()),
            user_id=user_id,
            type=form_data.type,
            status=form_data.status,
            input=(form_data.input.model_dump() if form_data.input else None),
            output=(form_data.output.model_dump() if form_data.output else None),
            parameters=(form_data.parameters.model_dump() if form_data.parameters else None),
            created_at=int(time.time()),
            updated_at=int(time.time()),
        )
        db.add(result)
        await db.commit()
        await db.refresh(result)
        return TaskModel.model_validate(result)

    async def get_task_by_id(self, db: AsyncSession, task_id: str) -> Optional[TaskModel]:
        task = await db.execute(select(Task).filter(Task.id == task_id))
        task = task.scalar_one_or_none()
        if not task:
            logger.warning(f"Task with id {task_id} not found.")
            return None
        return TaskModel.model_validate(task)

    async def update_task(self, db: AsyncSession, task_id: str, form_data: TaskUpdateForm) -> Optional[TaskModel]:
        task = await db.execute(select(Task).filter(Task.id == task_id))
        task = task.scalar_one_or_none()
        if not task:
            logger.warning(f"Task with id {task_id} not found.")
            return None

        # Nettoyer les parameters pour enlever le token
        cleaned_form_data = form_data.model_copy()
        if cleaned_form_data.parameters and cleaned_form_data.parameters.headers:
            cleaned_headers = {k: v for k, v in cleaned_form_data.parameters.headers.items() if k.lower() != "authorization"}
            cleaned_form_data.parameters.headers = cleaned_headers

        updates = cleaned_form_data.model_dump(exclude_unset=True)
        for key, value in updates.items():
            if hasattr(task, key):
                setattr(task, key, value)

        if cleaned_form_data.output:
            task.output = cleaned_form_data.output.model_dump()
        if cleaned_form_data.input:
            task.input = cleaned_form_data.input.model_dump()
        if cleaned_form_data.parameters:
            # Correction: était form_data.input
            task.parameters = cleaned_form_data.parameters.model_dump()

        await db.commit()
        await db.refresh(task)
        return TaskModel.model_validate(task)

    async def delete_task_by_id(self, db: AsyncSession, task_id: str) -> Optional[TaskModel]:
        task = await db.execute(select(Task).filter(Task.id == task_id))
        task = task.scalar_one_or_none()
        if not task:
            logger.warning(f"Task with id {task_id} not found.")
            return None
        await db.delete(task)
        await db.commit()
        return TaskModel.model_validate(task)

    async def get_tasks_by_user_id(self, db: AsyncSession, user_id: str, page: int = 1, page_size: int = 10) -> List[TaskModel]:
        offset = (page - 1) * page_size
        tasks = (await db.execute(select(Task).filter(Task.user_id == user_id).offset(offset).limit(page_size))).scalars().all()

        if not tasks:
            logger.warning(f"No tasks found for user {user_id}.")
            return []

        return [TaskModel.model_validate(task) for task in tasks]

    async def count_tasks_by_user_id(self, db: AsyncSession, user_id: str) -> int:
        count = (await db.execute(select(func.count(Task.id)).filter(Task.user_id == user_id))).scalar_one()
        return count

    async def delete_tasks_by_user_id(self, db: AsyncSession, user_id: str) -> Optional[List[TaskModel]]:
        tasks_to_delete = (await db.execute(select(Task).filter(Task.user_id == user_id))).scalars().all()

        if not tasks_to_delete:
            logger.warning(f"No tasks found for user {user_id}.")
            return None

        for task in tasks_to_delete:
            await db.delete(task)

        return [TaskModel.model_validate(task) for task in tasks_to_delete]

    async def get_position_in_queue(self, db: AsyncSession, task_id: str) -> int | None:
        if task_id:
            task = await db.execute(select(Task).filter(Task.id == task_id))
            task = task.scalar_one_or_none()
            if not task:
                return None

            if task.status != TaskStatus.QUEUED:
                return None

            position = (
                await db.execute(
                    select(func.count(Task.id)).filter(  # noqa
                        Task.status == TaskStatus.QUEUED,
                        Task.created_at < task.created_at,
                    )
                )
            ).scalar_one()

            return position

    async def search_task_by_fields(self, db: AsyncSession, **filters) -> Optional[TaskModel]:
        query = select(Task)
        for field, value in filters.items():
            if hasattr(Task, field):
                query = query.filter(getattr(Task, field) == value)
        task = await db.execute(query)
        task = task.scalar_one_or_none()
        return TaskModel.model_validate(task) if task else None

    async def statistics(
        self,
        db: AsyncSession,
        user_id: str,
        is_admin: bool = False,
        skip: int = 0,
        limit: int = 10,
    ) -> TaskStats:
        # Statistiques globales
        total_tasks = (await db.execute(select(func.count(Task.id)))).scalar_one()

        tasks_stats = (await db.execute(select(Task.status, func.count(Task.id)).group_by(Task.status))).all()
        tasks_stats_dict = {status: count for status, count in tasks_stats}

        global_stats = TaskStatsGlobal(total_tasks=total_tasks, tasks_stats=tasks_stats_dict)

        # Statistiques de l'utilisateur courant
        user_total_tasks = (await db.execute(select(func.count(Task.id)).filter(Task.user_id == user_id))).scalar_one()

        user_tasks_stats = (await db.execute(select(Task.status, func.count(Task.id)).filter(Task.user_id == user_id).group_by(Task.status))).all()
        user_tasks_stats_dict = {status: count for status, count in user_tasks_stats}
        user_stats = TaskStatsUser(
            user_id=user_id,
            total_tasks=user_total_tasks,
            tasks_stats=user_tasks_stats_dict,
        )

        # Statistiques par utilisateur (paginated)
        user_stats_list = []
        if is_admin:
            user_stats_count = (await db.execute(select(func.count(func.distinct(Task.user_id))))).scalar_one()

            user_stats_query = (await db.execute(select(Task.user_id, func.count(Task.id)).group_by(Task.user_id).offset(skip).limit(limit))).all()

            for uid, count in user_stats_query:
                per_user_stats = (await db.execute(select(Task.status, func.count(Task.id)).filter(Task.user_id == uid).group_by(Task.status))).all()
                per_user_stats_dict = {status: count for status, count in per_user_stats}
                user_stats_list.append(
                    TaskStatsUser(
                        user_id=uid,
                        total_tasks=count,
                        tasks_stats=per_user_stats_dict,
                    )
                )
        pagination_stats = Pagination[TaskStatsUser](
            total=user_stats_count,
            page=skip // limit + 1,
            page_size=limit,
            items=user_stats_list,
        )

        return TaskStats(
            global_stats=global_stats,
            all_users_stats=pagination_stats,
            user_stats=user_stats,
        )

    async def count_unique_users_between_dates(self, db: AsyncSession, start_date: int, end_date: int) -> int:
        result = await db.execute(select(func.count(func.distinct(Task.user_id))).filter(Task.created_at >= start_date, Task.created_at <= end_date))
        return result.scalar_one()
