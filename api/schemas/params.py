from typing import Literal, Annotated
from pydantic import BaseModel
from fastapi import Query

MethodType = Literal["map_reduce", "refine", "text_rank", "k-means", "stuff"]  # "text_rank2", "k-means2"
ChunkType = Literal["sentences", "chunks"]


class ParamsSummarize(BaseModel):
    method: MethodType | None = "map_reduce"
    model: str = "chat-leger"
    context_size: int | None = 10_000
    temperature: Annotated[float, Query(ge=0, le=1.0)] = 0.
    language: str | None = "French"
    size: int | None = 4_000
    # summarize_template: str | None = (None,)
    # map_template: str | None = (None,)
    # reduce_template: str | None = (None,)
    # question_template: str | None = (None,)
    # refine_template: str | None = (None,)
    custom_prompt: str | None = "en français"
