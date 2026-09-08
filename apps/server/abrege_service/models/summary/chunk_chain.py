from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

# Prompt pour le découpage sémantique : au lieu d'un découpage par nombre de mots/tokens,
# on demande au modèle de trouver les frontières où le sujet change.
chunk_template = """The following is a text extract:
{text}
Split this extract into semantically coherent chunks: group sentences or paragraphs that belong to the same idea or topic together, and start a new chunk whenever the topic clearly shifts. Preserve the original text exactly (do not summarize, translate or alter it) — only decide where to cut. If the whole extract is already about a single coherent topic, return it as a single chunk.
Respond ONLY with a valid JSON object matching this schema: {{"chunks": ["...", "..."]}}"""

CHUNK_PROMPT = PromptTemplate(template=chunk_template, input_variables=["text"])


class ChunkingOutput(BaseModel):
    chunks: list[str] = Field(
        description="The extract split into semantically coherent chunks, in original order, text preserved verbatim",
        default_factory=list,
    )


def build_chunk_runnable(llm: ChatOpenAI) -> Runnable:
    return CHUNK_PROMPT | llm.with_structured_output(ChunkingOutput, method="json_mode")
