from abrege_service.models.summary.definitions import (
    build_entities_instructions,
    build_topics_instructions,
    format_entity_definitions,
    format_topic_definitions,
)
from abrege_service.models.summary.entity_chain import ENTITY_PROMPT
from abrege_service.models.summary.topic_chain import TOPIC_PROMPT
from src.schemas.parameters import EntityDefinition, SummaryParameters, TopicDefinition


def test_empty_definitions_format_to_empty_string():
    assert format_entity_definitions(None) == ""
    assert format_entity_definitions([]) == ""
    assert format_topic_definitions(None) == ""
    assert format_topic_definitions([]) == ""


def test_entity_definitions_render_name_type_definition_and_examples():
    text = format_entity_definitions(
        [
            EntityDefinition(name="date_signature", type="date", definition="Date de signature du contrat", examples=["12/03/2024", "1er mai 2023"]),
            EntityDefinition(name="statut", type="enum", enum_values=["ouvert", "fermé"]),
            EntityDefinition(name="montant", type="number"),
        ]
    )
    assert "- date_signature (a date (ISO 8601 when possible)): Date de signature du contrat Examples: 12/03/2024; 1er mai 2023." in text
    assert "- statut (one of: ouvert, fermé)" in text
    assert "- montant (a number)" in text
    assert "montant (a number):" not in text


def test_topic_definitions_render_name_definition_and_examples():
    text = format_topic_definitions(
        [
            TopicDefinition(name="recrutement", definition="Offres d'emploi et entretiens", examples=["CDI", "fiche de poste"]),
            TopicDefinition(name="paie"),
        ]
    )
    assert "- recrutement: Offres d'emploi et entretiens Examples: CDI; fiche de poste." in text
    assert "- paie" in text
    assert "paie:" not in text


def test_build_instructions_without_definitions_keeps_free_text_unchanged():
    params = SummaryParameters(entities_instructions="ignore les lieux", topics_instructions="catégories RH")
    assert build_entities_instructions(params) == "ignore les lieux"
    assert build_topics_instructions(params) == "catégories RH"
    assert build_entities_instructions(SummaryParameters()) == ""
    assert build_topics_instructions(SummaryParameters()) == ""


def test_build_instructions_merges_free_text_and_definitions():
    params = SummaryParameters(
        entities_instructions="ignore les lieux",
        entity_definitions=[EntityDefinition(name="montant", type="number")],
        topics_instructions="catégories RH",
        topic_definitions=[TopicDefinition(name="paie")],
    )
    entities = build_entities_instructions(params)
    topics = build_topics_instructions(params)
    assert entities.startswith("ignore les lieux\n")
    assert "- montant (a number)" in entities
    assert topics.startswith("catégories RH\n")
    assert "- paie" in topics


def test_definitions_reach_the_entity_and_topic_prompts():
    params = SummaryParameters(
        entity_definitions=[EntityDefinition(name="montant", type="number", definition="Somme en euros")],
        topic_definitions=[TopicDefinition(name="paie", definition="Salaires et bulletins")],
    )
    entity_prompt = ENTITY_PROMPT.format(text="Le loyer est de 800 €.", language="French", instructions=build_entities_instructions(params))
    topic_prompt = TOPIC_PROMPT.format(text="Résumé RH.", language="French", instructions=build_topics_instructions(params))
    assert "- montant (a number): Somme en euros" in entity_prompt
    assert "- paie: Salaires et bulletins" in topic_prompt


def test_entity_definitions_focus_extraction_on_the_listed_entities_only():
    text = format_entity_definitions([EntityDefinition(name="montant", type="number")])
    assert "ONLY" in text
    assert "Do NOT extract or mention any other entity" in text
    assert "If none matches, return no entities" in text


def test_entity_definitions_restrict_relationships_to_extracted_entities():
    text = format_entity_definitions([EntityDefinition(name="montant", type="number")])
    assert "Relationships must only link entities you actually extracted" in text


def test_entity_focus_reaches_the_chunk_and_global_relationship_prompts():
    from abrege_service.models.summary.entity_chain import GLOBAL_RELATIONSHIP_PROMPT

    params = SummaryParameters(entity_definitions=[EntityDefinition(name="montant", type="number")])
    instructions = build_entities_instructions(params)
    chunk_prompt = ENTITY_PROMPT.format(text="t", language="French", instructions=instructions)
    global_prompt = GLOBAL_RELATIONSHIP_PROMPT.format(entities_list="0: montant - 800 - pages [1]", instructions=instructions)
    for prompt in (chunk_prompt, global_prompt):
        assert "Extract ONLY entities matching one of these definitions" in prompt
        assert "Relationships must only link entities you actually extracted" in prompt


def test_no_focus_wording_without_entity_definitions():
    params = SummaryParameters(entities_instructions="ignore les lieux")
    assert "ONLY" not in build_entities_instructions(params)
