from pydantic import BaseModel, ConfigDict, Field
import uuid


class MergeTask(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    merge_id: str
    related_task: str
    type: str
    status: str = "queued"
    user_id: str
    group_id: str | None = None
    percentage: float = 0.0
    position: int | None = -1

    created_at: int
    updated_at: int

    extras: dict | None = Field(default_factory=dict)


class MergeTaskCreateForm(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    merge_id: str
    related_task: str
    type: str
    user_id: str
    group_id: str | None = None
    position: int | None = -1

    extras: dict | None = Field(default_factory=dict)


class MergeTaskUpdateForm(BaseModel):
    status: str | None = None
    percentage: float | None = None
    position: int | None = None

    extras: dict | None = Field(default_factory=dict)
