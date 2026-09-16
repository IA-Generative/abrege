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
    headers: dict | None = Field(default_factory=dict, description="Headers to include in the request")


class SummaryParameters(BaseParameters):
    method: MethodType | None = "map_reduce"
    custom_prompt: str | None = Field(None, description="Custom prompt you want after the sumup")
    extract_qa: bool = Field(False, description="Also generate question/answer pairs per chunk while summarizing")
    qa_per_chunk: int = Field(3, ge=0, le=10, description="Max number of question/answer pairs to generate per chunk when extract_qa is enabled")
    qa_instructions: str | None = Field(None, description="Extra instruction for the Q&A generation, used only when extract_qa is enabled")
    extract_entities: bool = Field(False, description="Also extract entities and relationships (per chunk, then cross-chunk) while summarizing")
    entities_instructions: str | None = Field(
        None, description="Extra instruction for entity/relationship extraction, used only when extract_entities is enabled"
    )
    extract_chunks: bool = Field(False, description="Also persist the semantic sub-chunks produced while summarizing")
    chunks_instructions: str | None = Field(None, description="Extra instruction for the semantic chunking, used only when extract_chunks is enabled")
    classify_topics: bool = Field(False, description="Classify the final summary into free-form topics")
    topics_instructions: str | None = Field(None, description="Extra instruction for topic classification, used only when classify_topics is enabled")
