import pytest
from pydantic import ValidationError

from src.schemas.parameters import EntityDefinition, SummaryParameters, TopicDefinition


def test_definitions_default_to_none():
    params = SummaryParameters()
    assert params.entity_definitions is None
    assert params.topic_definitions is None


def test_entity_definition_defaults_and_cleaning():
    entity = EntityDefinition(name="  date_signature ", definition="  ", examples=[" 12/03/2024 ", "", "  "])
    assert entity.name == "date_signature"
    assert entity.type == "string"
    assert entity.definition is None
    assert entity.examples == ["12/03/2024"]


def test_entity_definition_rejects_blank_name():
    with pytest.raises(ValidationError):
        EntityDefinition(name="   ")


def test_entity_definition_rejects_unknown_type():
    with pytest.raises(ValidationError):
        EntityDefinition(name="x", type="color")


def test_enum_entity_requires_values():
    with pytest.raises(ValidationError):
        EntityDefinition(name="statut", type="enum")
    with pytest.raises(ValidationError):
        EntityDefinition(name="statut", type="enum", enum_values=["  ", ""])


def test_enum_entity_cleans_values():
    entity = EntityDefinition(name="statut", type="enum", enum_values=[" ouvert ", "fermé", ""])
    assert entity.enum_values == ["ouvert", "fermé"]


def test_entity_names_must_be_unique_case_insensitive():
    with pytest.raises(ValidationError, match="Duplicate entity name"):
        SummaryParameters(entity_definitions=[{"name": "Date"}, {"name": "date"}])


def test_topic_names_must_be_unique_case_insensitive():
    with pytest.raises(ValidationError, match="Duplicate topic name"):
        SummaryParameters(topic_definitions=[{"name": "Finance"}, {"name": "finance "}])


def test_definitions_are_capped():
    with pytest.raises(ValidationError):
        SummaryParameters(topic_definitions=[{"name": f"t{i}"} for i in range(51)])
    with pytest.raises(ValidationError):
        TopicDefinition(name="t", examples=[str(i) for i in range(21)])


def test_parameters_roundtrip_from_frontend_json_payload():
    payload = (
        '{"extract_entities": true, "entity_definitions": ['
        '{"name": "montant", "type": "number", "definition": "Somme en euros", "examples": ["1 200 €"], "enum_values": []}],'
        ' "classify_topics": true, "topic_definitions": [{"name": "finance", "definition": null, "examples": []}]}'
    )
    params = SummaryParameters.model_validate_json(payload)
    assert params.entity_definitions[0].type == "number"
    assert params.topic_definitions[0].name == "finance"
    assert SummaryParameters.model_validate(params.model_dump()) == params
