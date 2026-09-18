from typing import Optional
from pydantic import BaseModel, ConfigDict


class QAItemRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    task_id: str
    chunk_index: int
    page: Optional[int] = None
    source_text: str
    question: str
    answer: str
    model_name: Optional[str] = None
    created_at: int
