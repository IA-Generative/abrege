from typing import Dict, Optional, Any, List
from pydantic import BaseModel, ConfigDict


class ResultModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    type: str
    created_at: int
    model_name: str
    model_version: str
    updated_at: Optional[int] = None
    texts_found: Optional[List[str]] = []
    percentage: float = 0.0
    extras: Optional[Dict[str, Any]] = None


class SummaryModel(ResultModel):
    summary: str
    word_count: int
    type: str = "summary"
