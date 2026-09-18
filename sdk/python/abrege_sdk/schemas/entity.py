from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class EntityRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    task_id: str
    chunk_index: int
    type: str
    text: str
    contexts: Optional[List[str]] = None
    pages: Optional[List[int]] = None
    model_name: Optional[str] = None
    created_at: int


class RelationshipRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    task_id: str
    chunk_index: Optional[int] = None
    source_entity_id: str
    target_entity_id: str
    relationship_type: str
    description: Optional[str] = None
    model_name: Optional[str] = None
    created_at: int
