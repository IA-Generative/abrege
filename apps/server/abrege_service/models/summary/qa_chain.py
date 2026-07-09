import re
from typing import Union

from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

# Prompt pour la génération optionnelle de questions/réponses, en plus du résumé, sur un même chunk.
qa_template = """The following is a text extract:
{text}
Generate at most {qa_per_chunk} question-answer pairs strictly based on this text extract.
Each answer must be directly supported by the text — do not invent or infer facts that are not present.
If the text does not contain enough substantive content to generate meaningful questions, return fewer pairs (or none).
Respond ONLY with a valid JSON object matching this schema: {{"items": [{{"question": "...", "answer": "..."}}]}}
Questions and answers in {language}:"""

QA_PROMPT = PromptTemplate(
    template=qa_template,
    input_variables=["text", "language", "qa_per_chunk"],
)


class QAItemOutput(BaseModel):
    question: str = Field(description="A question generated from the text extract")
    answer: str = Field(description="The answer to the question, strictly grounded in the text extract")


class QAOutput(BaseModel):
    items: list[QAItemOutput] = Field(
        description="A list of question-answer pairs generated from the text extract",
        default_factory=list,
    )


def build_qa_runnable(llm: ChatOpenAI) -> Runnable:
    return QA_PROMPT | llm.with_structured_output(QAOutput, method="json_mode")


def extract_leading_page_number(text: str) -> Union[int, None]:
    """Best-effort parse of the `PageN: ` prefix injected by the chunking utils."""
    match = re.match(r"\s*Page(\d+):", text)
    return int(match.group(1)) if match else None
