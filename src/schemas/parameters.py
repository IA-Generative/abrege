from typing import Literal
from pydantic import BaseModel

MethodType = Literal["map_reduce", "refine", "text_rank", "k-means", "stuff"]  # "text_rank2", "k-means2"

MAP_PROMPT = "Rédigez un résumé concis des éléments suivants :\\n\\n{context}"
REDUCE_PROMPT = """
Voici une série de résumés:
{docs}
Rassemblez ces éléments et faites-en un résumé final et consolidé dans {language} en {size} mots au maximum. Rédigez uniquement en {language}.
"""


class BaseParameters(BaseModel):
    temperature: float = 0.0
    language: str | None = "French"
    size: int | None = 4_000
    extras: dict | None = {}


class SummaryParameters(BaseParameters):
    method: MethodType | None = "map_reduce"
    model: str = "qwen2.5"
    context_size: int | None = 10_000
    map_prompt: str | None = MAP_PROMPT
    reduce_prompt: str | None = REDUCE_PROMPT
    extras: dict | None = {}
    custom_prompt: str | None = None
