from pydantic import BaseModel
from typing import List


class Words(BaseModel):
    """
    Model for words in audio processing.
    """

    word: str
    start: float
    end: float
    conf: float


class AudioModel(BaseModel):
    """
    Model for audio processing.
    """

    result: List[Words]
    text: str
