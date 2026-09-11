from abrege_sdk.schemas.parameters import SummaryParameters
from pydantic import BaseModel, ConfigDict
from typing import Optional, Any, Dict, Union


class ContentModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    type: str
    created_at: int
    extras: Optional[Dict[str, Any]] = None


class URLModel(ContentModel):
    url: str
    type: str = "url"
    file_path: Optional[str] = None
    raw_filename: Optional[str] = None
    content_type: Optional[str] = None
    ext: Optional[str] = None
    size: Optional[int] = None


class DocumentModel(ContentModel):
    file_path: str
    raw_filename: str
    content_type: str
    ext: str
    size: int
    type: str = "document"


class TextModel(ContentModel):
    text: str
    type: str = "texte"


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
    parameters: Optional[SummaryParameters] = SummaryParameters()


class Input(BaseModel):
    content: Optional[Union[UrlContent, TextContent, Content]] = Content()
    parameters: Optional[SummaryParameters] = SummaryParameters()
