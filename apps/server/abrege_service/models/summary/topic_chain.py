from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

# Prompt pour la classification libre des sujets/thèmes, appliquée au résumé final (pas au texte source).
topic_template = """The following is the summary of a document:
{text}
Identify the main topics/subjects this document is about. Topics are freely chosen — not restricted to a fixed list, and not entity names (no people, dates or organizations) but general subject areas or domains (e.g. "finance", "santé publique", "droit du travail"). There can be one or several topics; only include ones clearly supported by the summary.
For each topic, give a confidence score between 0 and 1 (how confident you are this is genuinely a topic of the document) and a short explanation grounded in the summary, justifying the classification.
Respond ONLY with a valid JSON object matching this schema: {{"topics": [{{"topic": "...", "confidence": 0.0, "explanation": "..."}}]}}
Answer in {language}:"""

TOPIC_PROMPT = PromptTemplate(template=topic_template, input_variables=["text", "language"])


class TopicOutput(BaseModel):
    topic: str = Field(description="A general subject/domain the document is about, freely worded")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence that this is genuinely a topic of the document, between 0 and 1")
    explanation: str = Field(description="Short explanation, grounded in the summary, justifying why this topic was assigned")


class TopicClassificationOutput(BaseModel):
    topics: list[TopicOutput] = Field(
        description="The topics/subjects the document is about, possibly several",
        default_factory=list,
    )


def build_topic_runnable(llm: ChatOpenAI) -> Runnable:
    return TOPIC_PROMPT | llm.with_structured_output(TopicClassificationOutput, method="json_mode")
