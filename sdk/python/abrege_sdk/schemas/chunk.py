from typing import Optional
from pydantic import BaseModel, ConfigDict


class ChunkRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    task_id: str
    chunk_index: int
    position: int
    page: Optional[int] = None
    text: str
    model_name: Optional[str] = None
    created_at: int
