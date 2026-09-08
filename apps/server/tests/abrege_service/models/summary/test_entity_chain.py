from unittest.mock import MagicMock

from langchain_core.runnables import Runnable

from abrege_service.models.summary.entity_chain import (
    ChunkEntitiesOutput,
    ChunkEntityOutput,
    ChunkRelationshipOutput,
    ENTITY_PROMPT,
    GLOBAL_RELATIONSHIP_PROMPT,
    GlobalRelationshipsOutput,
    build_entity_runnable,
    build_global_relationship_runnable,
)


def test_entity_prompt_formats_text_and_language():
    formatted = ENTITY_PROMPT.format(text="Marie Curie a reçu le prix Nobel.", language="French")
    assert "Marie Curie a reçu le prix Nobel." in formatted
    assert "French" in formatted


def test_global_relationship_prompt_formats_entities_list():
    formatted = GLOBAL_RELATIONSHIP_PROMPT.format(entities_list="0: PERSON - Alice - pages [1]")
    assert "0: PERSON - Alice - pages [1]" in formatted


def test_build_entity_runnable_returns_a_runnable():
    runnable = build_entity_runnable(MagicMock())
    assert isinstance(runnable, Runnable)


def test_build_global_relationship_runnable_returns_a_runnable():
    runnable = build_global_relationship_runnable(MagicMock())
    assert isinstance(runnable, Runnable)


def test_chunk_entities_output_defaults_to_empty_lists():
    output = ChunkEntitiesOutput()
    assert output.entities == []
    assert output.relationships == []


def test_chunk_entities_output_accepts_entities_and_relationships():
    output = ChunkEntitiesOutput(
        entities=[ChunkEntityOutput(type="PERSON", text="Alice", contexts=["ctx"])],
        relationships=[
            ChunkRelationshipOutput(source_index=0, target_index=0, relationship_type="SELF", description="desc")
        ],
    )
    assert len(output.entities) == 1
    assert output.entities[0].text == "Alice"
    assert len(output.relationships) == 1


def test_global_relationships_output_defaults_to_empty_list():
    assert GlobalRelationshipsOutput().relationships == []
