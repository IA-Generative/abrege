from unittest.mock import MagicMock

from langchain_core.runnables import Runnable

from abrege_service.models.summary.topic_chain import (
    TOPIC_PROMPT,
    TopicClassificationOutput,
    TopicOutput,
    build_topic_runnable,
)


def test_topic_prompt_formats_text_and_language():
    formatted = TOPIC_PROMPT.format(text="Le document traite de finance publique.", language="French")
    assert "Le document traite de finance publique." in formatted
    assert "French" in formatted


def test_build_topic_runnable_returns_a_runnable():
    runnable = build_topic_runnable(MagicMock())
    assert isinstance(runnable, Runnable)


def test_topic_classification_output_defaults_to_empty_list():
    assert TopicClassificationOutput().topics == []


def test_topic_classification_output_accepts_multiple_topics():
    output = TopicClassificationOutput(
        topics=[
            TopicOutput(topic="finance", confidence=0.9, explanation="e1"),
            TopicOutput(topic="santé publique", confidence=0.3, explanation="e2"),
        ]
    )
    assert len(output.topics) == 2
    assert output.topics[0].confidence == 0.9


def test_topic_output_confidence_is_bounded():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        TopicOutput(topic="finance", confidence=1.5, explanation="e")
    with pytest.raises(ValidationError):
        TopicOutput(topic="finance", confidence=-0.1, explanation="e")
