from typing import Optional, Any
from pydantic import BaseModel


class TextModel(BaseModel):
    text: str
    extras: Optional[dict[Any, Any]] = None
