from pydantic import BaseModel


class SummaryResponse(BaseModel):
    summary: str
    nb_call: int | None = None
    time: float | None = None
    nb_words: int | None = 0
