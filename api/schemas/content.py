from typing import Optional, Any, Dict, Union
from pydantic import BaseModel

from src.schemas.parameters import SummaryParameters


class Content(BaseModel):
    prompt: Optional[str] = None
    extras: Optional[Dict[str, Any]] = None


class UrlContent(Content):
    url: str


class TextContent(Content):
    text: str


class InputModel(BaseModel):
    user_id: str
    content: Optional[Union[UrlContent, TextContent, Content]] = Content()
    parameters: Optional[SummaryParameters] = None
