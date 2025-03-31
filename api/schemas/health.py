from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel


class HealthError(BaseModel):
    name: str
    error: str
    code_status: int


class Health(BaseModel):
    name: str
    version: str
    up_time: str
    extras: Optional[Dict[str, Any]] = None
    status: Literal["healthy", "healthy"] = "healthy"
    dependencies: Optional[List["Health"]] = None
