from typing import Dict, Optional, Any, Union
from enum import Enum, StrEnum
from pydantic import BaseModel, ConfigDict, Field

from src.schemas.content import URLModel, DocumentModel, TextModel, MergeModel
from src.schemas.result import ResultModel, SummaryModel
from src.schemas.parameters import SummaryParameters, ClassificationParameters
from src.schemas.pagination import Pagination


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
    REVOKED = "revoked"  # Révoquée via l’API de gestion des tâches (ex: Celery)


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
