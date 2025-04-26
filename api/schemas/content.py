from typing import Optional, Any, Dict
from pydantic import BaseModel


class Content(BaseModel):
    prompt: Optional[str] = None
    extras: Optional[Dict[str, Any]] = None


class UrlContent(Content):
    url: str


class TextContent(Content):
    text: str
