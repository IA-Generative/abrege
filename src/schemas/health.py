from __future__ import annotations
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from enum import Enum


class HealtStatus(str, Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"


class Health(BaseModel):
    name: str
    version: str
    up_time: str
    extras: Optional[Dict[str, Any]] = None
    status: HealtStatus = HealtStatus.HEALTHY.value
    dependencies: Optional[List[Health]] = None
