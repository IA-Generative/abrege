from typing import Optional
from pydantic import BaseModel, ConfigDict


class TopicRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    task_id: str
    topic: str
    confidence: float
    explanation: Optional[str] = None
    model_name: Optional[str] = None
    created_at: int
