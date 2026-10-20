from typing import Optional, Any, Dict, Union
from pydantic import BaseModel, Field

from src.schemas.parameters import SummaryParameters


class Content(BaseModel):
    prompt: Optional[str] = Field(None, description="Extra instruction appended after the summary request, e.g. \"use a formal tone\"")
    extras: Optional[Dict[str, Any]] = Field(None, description="Free-form extra information stored with the task")


class UrlContent(Content):
    url: str = Field(description="URL of the page or file to summarize (must be reachable by the service)")


class TextContent(Content):
    text: str = Field(description="Text to summarize")


class InputModel(BaseModel):
    user_id: str = Field(description="Owner of the task")
    content: Optional[Union[UrlContent, TextContent, Content]] = Field(Content(), description="What to summarize: a URL or a text")
    parameters: Optional[SummaryParameters] = Field(SummaryParameters(), description="Summary options")


class Input(BaseModel):
    content: Optional[Union[UrlContent, TextContent, Content]] = Field(Content(), description="What to summarize: a URL (`{\"url\": ...}`) or a text (`{\"text\": ...}`)")
    parameters: Optional[SummaryParameters] = Field(SummaryParameters(), description="Summary options, including the optional extractions (Q&A, entities, chunks, topics)")
