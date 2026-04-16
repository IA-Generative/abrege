from datetime import datetime
import uuid
import time
from typing import Dict, List, Optional, Any, Union
from enum import Enum, StrEnum
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Column, String, JSON, BigInteger, select, Float, Integer, func
from sqlalchemy.exc import SQLAlchemyError

from src.internal.db import get_db, Base
from src.schemas.content import URLModel, DocumentModel, TextModel, MergeModel
from src.schemas.result import ResultModel, SummaryModel
from src.schemas.parameters import SummaryParameters, ClassificationParameters
from src.schemas.pagination import Pagination
from src.utils.logger import logger_abrege as logger


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True)
    type = Column(String, nullable=False)
    status = Column(String, default="queued")
    user_id = Column(String, nullable=False)
    group_id = Column(String, nullable=True)
    percentage = Column(Float, nullable=False, default=0)
    position = Column(Integer, nullable=True)

    created_at = Column(BigInteger, default=lambda: int(datetime.now().timestamp()))
    updated_at = Column(
        BigInteger,
        default=lambda: int(datetime.now().timestamp()),
        onupdate=lambda: int(datetime.now().timestamp()),
    )
    input = Column(JSON, nullable=True)
    output = Column(JSON, nullable=True)
    parameters = Column(JSON, nullable=True)
    extras = Column(JSON, nullable=True)
    content_hash = Column(String, nullable=True, index=True, unique=False)


class TaskModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    user_id: str
    type: str
    status: str = "queued"
    group_id: Optional[str] = None
    percentage: Optional[float] = None
    input: Optional[Union[URLModel, DocumentModel, TextModel, MergeModel]] = None
    output: Optional[Union[ResultModel, SummaryModel]] = None
    parameters: Optional[Union[SummaryParameters, ClassificationParameters]] = SummaryParameters()
    position: Optional[int] = None

    created_at: int
    updated_at: int
    extras: Optional[Dict[str, Any]] = None
    content_hash: Optional[str] = None


class TaskForm(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    type: str
    status: Optional[str] = None
    percentage: Optional[float] = None
    position: Optional[int] = None
    input: Optional[Union[URLModel, DocumentModel, TextModel, MergeModel]] = None
    output: Optional[Union[ResultModel, SummaryModel]] = None
    parameters: Optional[Union[SummaryParameters, ClassificationParameters]] = None
    updated_at: Optional[int] = None
    extras: Optional[Dict[str, Any]] = None
    content_hash: Optional[str] = None


class TaskUpdateForm(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    status: Optional[str] = None
    percentage: Optional[float] = None
    position: Optional[int] = None
    input: Optional[Union[URLModel, DocumentModel, TextModel, MergeModel]] = None
    output: Optional[Union[ResultModel, SummaryModel]] = None
    parameters: Optional[Union[SummaryParameters, ClassificationParameters]] = None
    updated_at: Optional[int] = None
    extras: Optional[Dict[str, Any]] = None
    content_hash: Optional[str] = None


class TaskStatus(str, Enum):
    CREATED = "created"  # Tâche instanciée mais pas encore mise en file
    QUEUED = "queued"  # En attente dans une file de traitement
    STARTED = "started"  # A commencé à être traitée
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"  # Traitée avec succès
    FAILED = "failed"  # Erreur fatale
    RETRYING = "retrying"  # En cours de nouvelle tentative après échec
    CANCELED = "canceled"  # Annulée manuellement ou par logique métier
    TIMEOUT = "timeout"  # N’a pas pu terminer dans le temps imparti


class TaskStatsGlobal(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    total_tasks: int
    tasks_stats: Dict[TaskStatus, int]  # Clé = status, Valeur = nombre de tâches


class TaskStatsUser(TaskStatsGlobal):
    model_config = ConfigDict(from_attributes=True)
    user_id: str


class TaskStats(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    global_stats: TaskStatsGlobal
    user_stats: TaskStatsUser
    all_users_stats: Pagination[TaskStatsUser] = Field(None, description="Statistiques paginées pour tous les utilisateurs")


class TaskName(StrEnum):
    MERGE = "worker.tasks.merge-abrege"
    ABREGE = "worker.tasks.abrege"
    CLASSIFICATION = "worker.tasks.classification"


class TaskTable:
    def health_check(self) -> tuple[bool, Optional[str]]:
        with get_db() as db:
            try:
                db.execute(select(Task).limit(1))
                return True, None
            except SQLAlchemyError as e:
                return False, str(e)

    def insert_new_task(self, user_id: str, form_data: TaskForm) -> Optional[TaskModel]:
        with get_db() as db:
            # Nettoyer les parameters pour enlever le token
            cleaned_form_data = form_data.model_copy()
            if cleaned_form_data.parameters and cleaned_form_data.parameters.headers:
                cleaned_headers = {k: v for k, v in cleaned_form_data.parameters.headers.items() if k.lower() != "authorization"}
                cleaned_form_data.parameters.headers = cleaned_headers

            knowledge = TaskModel(
                **{
                    **cleaned_form_data.model_dump(),
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "created_at": int(time.time()),
                    "updated_at": int(time.time()),
                }
            )

            result = Task(**knowledge.model_dump())
            db.add(result)
            db.commit()
            db.refresh(result)
            return TaskModel.model_validate(result)

    def get_task_by_id(self, task_id: str) -> Optional[TaskModel]:
        with get_db() as db:
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task:
                logger.warning(f"Task with id {task_id} not found.")
                return None
            return TaskModel.model_validate(task)

    def update_task(self, task_id: str, form_data: TaskUpdateForm) -> Optional[TaskModel]:
        with get_db() as db:
            task = db.query(Task).filter(Task.id == task_id).first()
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

            task.updated_at = int(time.time())
            db.commit()
            db.refresh(task)
            return TaskModel.model_validate(task)

    def delete_task_by_id(self, task_id: str) -> Optional[TaskModel]:
        with get_db() as db:
            task = db.query(Task).filter(Task.id == task_id).first()
            if not task:
                logger.warning(f"Task with id {task_id} not found.")
                return None
            db.delete(task)
            db.commit()
            return TaskModel.model_validate(task)

    def get_tasks_by_user_id(self, user_id: str, page: int = 1, page_size: int = 10) -> Optional[List[TaskModel]]:
        offset = (page - 1) * page_size
        with get_db() as db:
            tasks = db.query(Task).filter(Task.user_id == user_id).offset(offset).limit(page_size).all()

            if not tasks:
                logger.warning(f"No tasks found for user {user_id}.")
                return []

            return [TaskModel.model_validate(task) for task in tasks]

    def count_tasks_by_user_id(self, user_id: str) -> int:
        with get_db() as db:
            count = db.query(func.count(Task.id)).filter(Task.user_id == user_id).scalar()
            return count

    def delete_tasks_by_user_id(self, user_id: str) -> Optional[List[TaskModel]]:
        with get_db() as db:
            tasks_to_delete = db.query(Task).filter(Task.user_id == user_id).all()

            if not tasks_to_delete:
                logger.warning(f"No tasks found for user {user_id}.")
                return None

            for task in tasks_to_delete:
                db.delete(task)
            db.commit()

            return [TaskModel.model_validate(task) for task in tasks_to_delete]

    def get_position_in_queue(self, task_id: str) -> int | None:
        if task_id:
            with get_db() as db:
                task = db.query(Task).filter(Task.id == task_id).first()
                if not task:
                    return None

                if task.status != TaskStatus.QUEUED:
                    return None

                position = (
                    db.query(func.count(Task.id))  # noqa
                    .filter(
                        Task.status == TaskStatus.QUEUED,
                        Task.created_at < task.created_at,
                    )
                    .scalar()
                )

                return position

    def search_task_by_fields(self, **filters) -> Optional[TaskModel]:
        with get_db() as db:
            query = db.query(Task)
            for field, value in filters.items():
                if hasattr(Task, field):
                    query = query.filter(getattr(Task, field) == value)
            task = query.first()
            return TaskModel.model_validate(task) if task else None

    def statistics(self, user_id: str, is_admin: bool = False, skip: int = 0, limit: int = 10) -> TaskStats:
        with get_db() as db:
            # statistiques User

            # Statistiques globales
            total_tasks = db.query(func.count(Task.id)).scalar()

            tasks_stats = (
                db.query(Task.status, func.count(Task.id))  # noqa
                .group_by(Task.status)
                .all()
            )
            tasks_stats_dict = {status: count for status, count in tasks_stats}

            global_stats = TaskStatsGlobal(total_tasks=total_tasks, tasks_stats=tasks_stats_dict)

            # Statistiques de l'utilisateur courant
            user_total_tasks = db.query(func.count(Task.id)).filter(Task.user_id == user_id).scalar()
            user_tasks_stats = (
                db.query(Task.status, func.count(Task.id))  # noqa
                .filter(Task.user_id == user_id)
                .group_by(Task.status)
                .all()
            )
            user_tasks_stats_dict = {status: count for status, count in user_tasks_stats}
            user_stats = TaskStatsUser(
                user_id=user_id,
                total_tasks=user_total_tasks,
                tasks_stats=user_tasks_stats_dict,
            )

            # Statistiques par utilisateur (paginated)
            user_stats_list = []
            pagination_stats = None
            if is_admin:
                user_stats_count = db.query(func.count(func.distinct(Task.user_id))).scalar()
                user_stats_query = (
                    db.query(Task.user_id, func.count(Task.id))  # noqa
                    .group_by(Task.user_id)
                    .offset(skip)
                    .limit(limit)
                    .all()
                )

                for user_id, count in user_stats_query:
                    user_tasks_stats = (
                        db.query(Task.status, func.count(Task.id))  # noqa
                        .filter(Task.user_id == user_id)
                        .group_by(Task.status)
                        .all()
                    )
                    user_tasks_stats_dict = {status: count for status, count in user_tasks_stats}
                    user_stats_list.append(
                        TaskStatsUser(
                            user_id=user_id,
                            total_tasks=count,
                            tasks_stats=user_tasks_stats_dict,
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

    def count_unique_users_between_dates(self, start_date: int, end_date: int) -> int:
        with get_db() as db:
            unique_users = db.query(Task.user_id).filter(Task.created_at >= start_date, Task.created_at <= end_date).distinct().count()
            return unique_users


task_table = TaskTable()
