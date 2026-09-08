from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

# Prompt pour l'extraction d'entités et de leurs relations locales, sur un même chunk.
entity_template = """The following is a text extract:
{text}
1. Extract the most important named entities: people, dates, organizations, locations, amounts, events.
2. Based on their contexts within this extract only, infer relationships between pairs of entities (0-based indices into the entities list). Only include relationships clearly supported by the text.
Respond ONLY with a valid JSON object matching this schema: {{"entities": [{{"type": "<the category you deem most appropriate, e.g. PERSON, DATE, ORGANIZATION, LOCATION, AMOUNT, EVENT, or any other relevant category>", "text": "...", "contexts": ["..."]}}], "relationships": [{{"source_index": 0, "target_index": 1, "relationship_type": "...", "description": "..."}}]}}
Answer in {language}:"""

ENTITY_PROMPT = PromptTemplate(template=entity_template, input_variables=["text", "language"])

# Prompt pour la passe finale de relations "globales", entre toutes les entités déjà extraites (cross-chunk).
global_relationship_template = """The following is a list of entities extracted from a document (index: type - text - pages):
{entities_list}
Based on their types, names and the pages where they appear, infer relationships between pairs of entities (0-based indices). Only include relationships clearly supported or plausible given the entities themselves. Aim to surface real, meaningful links across the whole document, not just within a single passage.
Respond ONLY with a valid JSON object matching this schema: {{"relationships": [{{"source_index": 0, "target_index": 1, "relationship_type": "...", "description": "..."}}]}}"""

GLOBAL_RELATIONSHIP_PROMPT = PromptTemplate(template=global_relationship_template, input_variables=["entities_list"])


class ChunkEntityOutput(BaseModel):
    type: str = Field(
        description="The category of the entity, freely chosen to best describe it (e.g. PERSON, DATE, ORGANIZATION, LOCATION, AMOUNT, EVENT, or any other relevant category)"
    )
    text: str = Field(description="The normalized text value of the entity (e.g. full name, ISO date, etc.)")
    contexts: list[str] = Field(
        description="All sentences or phrases where this entity was found in this extract",
        default_factory=list,
    )


class ChunkRelationshipOutput(BaseModel):
    source_index: int = Field(description="0-based index of the source entity in the entities list")
    target_index: int = Field(description="0-based index of the target entity in the entities list")
    relationship_type: str = Field(description="Type of relationship between the two entities")
    description: str = Field(description="Description of the relationship, including context and any relevant details")


class ChunkEntitiesOutput(BaseModel):
    entities: list[ChunkEntityOutput] = Field(
        description="A list of entities extracted from the text chunk",
        default_factory=list,
    )
    relationships: list[ChunkRelationshipOutput] = Field(
        description="A list of relationships between entities, inferred from their contexts within this chunk only",
        default_factory=list,
    )


class GlobalRelationshipsOutput(BaseModel):
    relationships: list[ChunkRelationshipOutput] = Field(
        description="A list of relationships between entities, inferred across the whole document",
        default_factory=list,
    )


def build_entity_runnable(llm: ChatOpenAI) -> Runnable:
    return ENTITY_PROMPT | llm.with_structured_output(ChunkEntitiesOutput, method="json_mode")


def build_global_relationship_runnable(llm: ChatOpenAI) -> Runnable:
    return GLOBAL_RELATIONSHIP_PROMPT | llm.with_structured_output(GlobalRelationshipsOutput, method="json_mode")
