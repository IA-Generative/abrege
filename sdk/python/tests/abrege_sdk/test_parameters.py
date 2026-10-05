import pytest
from pydantic import ValidationError

from abrege_sdk.schemas.parameters import EntityDefinition, SummaryParameters, TopicDefinition


def test_definitions_default_to_none():
    params = SummaryParameters()
    assert params.entity_definitions is None
    assert params.topic_definitions is None
    assert params.qa_instructions is None
    assert params.entities_instructions is None
    assert params.chunks_instructions is None
    assert params.topics_instructions is None


def test_instructions_are_accepted():
    params = SummaryParameters(
        qa_instructions="questions chiffrées",
        entities_instructions="ignore les lieux",
        chunks_instructions="par section",
        topics_instructions="catégories RH",
    )
    assert params.entities_instructions == "ignore les lieux"
    assert params.topics_instructions == "catégories RH"


def test_entity_definition_defaults_and_cleaning():
    entity = EntityDefinition(name="  date_signature ", definition="  ", examples=[" 12/03/2024 ", "", "  "])
    assert entity.name == "date_signature"
    assert entity.type == "string"
    assert entity.definition is None
    assert entity.examples == ["12/03/2024"]


def test_entity_definition_rejects_blank_name_and_unknown_type():
    with pytest.raises(ValidationError):
        EntityDefinition(name="   ")
    with pytest.raises(ValidationError):
        EntityDefinition(name="x", type="color")


def test_enum_entity_requires_values():
    with pytest.raises(ValidationError):
        EntityDefinition(name="statut", type="enum")
    assert EntityDefinition(name="statut", type="enum", enum_values=[" ouvert ", ""]).enum_values == ["ouvert"]


def test_names_must_be_unique_case_insensitive():
    with pytest.raises(ValidationError, match="Duplicate entity name"):
        SummaryParameters(entity_definitions=[{"name": "Date"}, {"name": "date"}])
    with pytest.raises(ValidationError, match="Duplicate topic name"):
        SummaryParameters(topic_definitions=[{"name": "Finance"}, {"name": "finance "}])


def test_definitions_are_capped():
    with pytest.raises(ValidationError):
        SummaryParameters(topic_definitions=[{"name": f"t{i}"} for i in range(51)])
    with pytest.raises(ValidationError):
        TopicDefinition(name="t", examples=[str(i) for i in range(21)])


def test_parameters_serialize_the_way_the_api_expects():
    params = SummaryParameters(
        extract_entities=True,
        entity_definitions=[EntityDefinition(name="montant", type="number", definition="Somme en euros", examples=["1 200 €"])],
        classify_topics=True,
        topic_definitions=[TopicDefinition(name="finance")],
    )
    dumped = params.model_dump(mode="json")
    assert dumped["entity_definitions"] == [
        {"name": "montant", "definition": "Somme en euros", "examples": ["1 200 €"], "type": "number", "enum_values": []}
    ]
    assert dumped["topic_definitions"] == [{"name": "finance", "definition": None, "examples": []}]
    assert SummaryParameters.model_validate_json(params.model_dump_json()) == params
