from src.schemas.parameters import EntityDefinition, SummaryParameters, TopicDefinition

_TYPE_HINTS = {
    "string": "free text",
    "number": "a number",
    "date": "a date (ISO 8601 when possible)",
    "boolean": "a boolean (true/false)",
}


def _join(*blocks: str) -> str:
    return "\n".join(block for block in blocks if block)


def format_entity_definitions(definitions: list[EntityDefinition] | None) -> str:
    if not definitions:
        return ""
    lines = [
        "FOCUS: the user is only interested in the entities listed below. This overrides the generic list of entity categories above.",
        "- Extract ONLY entities matching one of these definitions, and use the listed name, unchanged, as the entity's `type`.",
        "- Do NOT extract or mention any other entity, even an important one. If none matches, return no entities.",
        "- Relationships must only link entities you actually extracted from this list. Never create a relationship involving anything else.",
        "Entities:",
    ]
    for entity in definitions:
        type_hint = f"one of: {', '.join(entity.enum_values)}" if entity.type == "enum" else _TYPE_HINTS[entity.type]
        line = f"- {entity.name} ({type_hint})"
        if entity.definition:
            line += f": {entity.definition}"
        if entity.examples:
            line += f" Examples: {'; '.join(entity.examples)}."
        lines.append(line)
    return "\n".join(lines)


def format_topic_definitions(definitions: list[TopicDefinition] | None) -> str:
    if not definitions:
        return ""
    lines = [
        "The user expects these topics. Prefer them over inventing new ones, and only assign a topic when the summary clearly supports it:",
    ]
    for topic in definitions:
        line = f"- {topic.name}"
        if topic.definition:
            line += f": {topic.definition}"
        if topic.examples:
            line += f" Examples: {'; '.join(topic.examples)}."
        lines.append(line)
    return "\n".join(lines)


def build_entities_instructions(params: SummaryParameters) -> str:
    return _join(params.entities_instructions or "", format_entity_definitions(params.entity_definitions))


def build_topics_instructions(params: SummaryParameters) -> str:
    return _join(params.topics_instructions or "", format_topic_definitions(params.topic_definitions))
