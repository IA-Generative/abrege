from typing import Dict, Optional, Any, Union
from enum import Enum
from pydantic import BaseModel, ConfigDict

from abrege_sdk.schemas.content import URLModel, DocumentModel, TextModel
from abrege_sdk.schemas.result import ResultModel, SummaryModel
from abrege_sdk.schemas.parameters import SummaryParameters


class TaskModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    user_id: str
    type: str
    status: str = "queued"
    group_id: Optional[str] = None
    percentage: Optional[float] = None
    input: Optional[Union[URLModel, DocumentModel, TextModel]] = None
    output: Optional[Union[SummaryModel, ResultModel]] = None
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
    output: Optional[Union[SummaryModel, ResultModel]] = None
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
    output: Optional[Union[SummaryModel, ResultModel]] = None
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
