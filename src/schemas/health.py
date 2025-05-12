from __future__ import annotations
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel

from enum import Enum


class HealtStatus(str, Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"


class HealthError(BaseModel):
    name: str
    error: str
    code_status: int


class Health(BaseModel):
    name: str
    version: str
    up_time: str
    extras: Optional[Dict[str, Any]] = None
    status: HealtStatus = HealtStatus.HEALTHY.value
    dependencies: Optional[List[Union[Health, HealthError]]] = None
