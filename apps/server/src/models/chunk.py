from typing import List

from pydantic import BaseModel, ConfigDict, Field


class ChunkBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    storage_path: str
    content_hash: str
    text: str
    user_id: str
    group_id: str | None = None
    model_name: str
    vector: List[float]
    vector_size: int
    extras: dict | None = None


class ChunkModel(ChunkBase):
    id: str
    created_at: int


class ChunkUpsertForm(BaseModel):
    """Payload sent by the client to index a batch of chunks for a file."""

    chunks: List[ChunkBase] = Field(default_factory=list)


class ChunkSearchRequest(BaseModel):
    """Payload for semantic search over a file\'s chunks."""

    query_vector: List[float] = Field(..., description="Dense query embedding")
    top_k: int | None = Field(default=None, ge=1, le=50)
    threshold: float | None = Field(
        default=None,
        ge=-1.0,
        le=1.0,
        description="Minimum cosine similarity score for a chunk to be included in results",
    )


class ChunkSearchResult(BaseModel):
    """A single search hit returned to the client."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    content_hash: str
    text: str
    model_name: str
    score: float
    storage_path: str
