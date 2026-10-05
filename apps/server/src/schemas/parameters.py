from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator, model_validator

MethodType = Literal["map_reduce", "refine", "text_rank", "k-means", "stuff"]  # "text_rank2", "k-means2"


MAX_DEFINITIONS = 50
MAX_EXAMPLES = 20

EntityValueType = Literal["string", "number", "date", "boolean", "enum"]


def _check_unique_names(definitions: list | None, label: str) -> list | None:
    if not definitions:
        return definitions
    seen: set[str] = set()
    for definition in definitions:
        key = definition.name.casefold()
        if key in seen:
            raise ValueError(f"Duplicate {label} name: {definition.name!r}")
        seen.add(key)
    return definitions


class _Definition(BaseModel):
    name: str = Field(min_length=1, max_length=100, description="Name of the definition")
    definition: str | None = Field(None, max_length=1000, description="What the model should look for")
    examples: list[str] = Field(default_factory=list, max_length=MAX_EXAMPLES, description="Concrete examples")

    @field_validator("name", mode="before")
    @classmethod
    def _strip_name(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("definition", mode="before")
    @classmethod
    def _blank_definition_is_none(cls, value):
        if isinstance(value, str):
            return value.strip() or None
        return value

    @field_validator("examples", mode="after")
    @classmethod
    def _clean_examples(cls, value: list[str]) -> list[str]:
        return [example.strip() for example in value if example.strip()]


class EntityDefinition(_Definition):
    type: EntityValueType = Field("string", description="Expected value type of the entity")
    enum_values: list[str] = Field(default_factory=list, max_length=MAX_DEFINITIONS, description="Allowed values, for the 'enum' type")

    @field_validator("enum_values", mode="after")
    @classmethod
    def _clean_enum_values(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item.strip()]

    @model_validator(mode="after")
    def _enum_needs_values(self):
        if self.type == "enum" and not self.enum_values:
            raise ValueError(f"Entity {self.name!r} has type 'enum' but no enum_values")
        return self


class TopicDefinition(_Definition):
    pass


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
    entity_definitions: list[EntityDefinition] | None = Field(
        None,
        max_length=MAX_DEFINITIONS,
        description="Entities the user expects (name, type, definition, examples), used only when extract_entities is enabled",
    )
    topic_definitions: list[TopicDefinition] | None = Field(
        None,
        max_length=MAX_DEFINITIONS,
        description="Topics the user expects (name, definition, examples), used only when classify_topics is enabled",
    )

    @field_validator("entity_definitions", mode="after")
    @classmethod
    def _unique_entity_names(cls, value):
        return _check_unique_names(value, "entity")

    @field_validator("topic_definitions", mode="after")
    @classmethod
    def _unique_topic_names(cls, value):
        return _check_unique_names(value, "topic")
