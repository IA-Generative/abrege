from __future__ import annotations
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from enum import Enum


class HealtStatus(str, Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"


class Health(BaseModel):
    name: str = Field(..., description="Api name")
    version: str = Field(..., description="version name")
    up_time: str = Field(..., description="Since up time name")
    extras: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Any extras informations")
    status: HealtStatus = Field(HealtStatus.HEALTHY.value, description="Status of the api")
    dependencies: Optional[List[Health]] = Field(default_factory=list, description="List of dependencies of the api")
