from datetime import datetime
import uuid
import time
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from pydantic import BaseModel, ConfigDict
from sqlalchemy import Column, String, JSON, BigInteger, select, Float, Integer, func
from sqlalchemy.exc import SQLAlchemyError

from src.internal.db import get_db, Base
from src.schemas.content import URLModel, DocumentModel, TextModel
from src.schemas.result import ResultModel, SummaryModel
from src.schemas.parameters import SummaryParameters
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
    input: Optional[Union[URLModel, DocumentModel, TextModel]] = None
    output: Optional[Union[ResultModel, SummaryModel]] = None
    parameters: Optional[SummaryParameters] = SummaryParameters()
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
    input: Optional[Union[URLModel, DocumentModel, TextModel]] = None
    output: Optional[Union[ResultModel, SummaryModel]] = None
    parameters: Optional[SummaryParameters] = None
    updated_at: Optional[int] = None
    extras: Optional[Dict[str, Any]] = None
    content_hash: Optional[str] = None


class TaskUpdateForm(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    status: Optional[str] = None
    percentage: Optional[float] = None
    position: Optional[int] = None
    input: Optional[Union[URLModel, DocumentModel, TextModel]] = None
    output: Optional[Union[ResultModel, SummaryModel]] = None
    parameters: Optional[SummaryParameters] = None
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


class TaskTable:
    def health_check(self) -> bool:
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
                task.parameters = cleaned_form_data.parameters.model_dump()  # Correction: était form_data.input

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
                return None

            return [TaskModel.model_validate(task) for task in tasks]

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


task_table = TaskTable()
