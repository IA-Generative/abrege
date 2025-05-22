from typing import Literal, Optional
from pydantic import BaseModel, Field

MethodType = Literal["map_reduce", "refine", "text_rank", "k-means", "stuff"]  # "text_rank2", "k-means2"


class BaseParameters(BaseModel):
    temperature: Optional[float] = Field(0.0, ge=0.0, le=1.0, description="Temperature of the model")
    language: str | None = Field("French", description="Language you want the summary")
    size: int | None = Field(
        4_000,
        description="Number of words you, WARNING: the model will try to get less than the size",
    )
    extras: dict | None = Field(default_factory=dict, description="Extras informations")


class SummaryParameters(BaseParameters):
    method: MethodType | None = "map_reduce"
    custom_prompt: str | None = Field(None, description="Custom prompt you want after the sumup")
