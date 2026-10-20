from typing import Dict, Optional, Any
from pydantic import BaseModel, ConfigDict, Field


class ContentModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    type: str = Field(description="Kind of input (`url`, `document` or `texte`)")
    created_at: int = Field(description="Creation time, Unix timestamp (seconds)")
    extras: Optional[Dict[str, Any]] = Field(None, description="Free-form extra information provided with the input")


class URLModel(ContentModel):
    url: str = Field(description="URL of the page or file to summarize")
    type: str = Field("url", description="Always `url`")
    file_path: Optional[str] = Field(None, description="Storage path of the downloaded file, once fetched")
    raw_filename: Optional[str] = Field(None, description="Original file name, once fetched")
    content_type: Optional[str] = Field(None, description="MIME type of the downloaded content")
    ext: Optional[str] = Field(None, description="File extension of the downloaded content")
    size: Optional[int] = Field(None, description="Size of the downloaded content, in bytes")


class DocumentModel(ContentModel):
    file_path: str = Field(description="Storage path of the uploaded file")
    raw_filename: str = Field(description="Original name of the uploaded file")
    content_type: str = Field(description="MIME type of the uploaded file")
    ext: str = Field(description="File extension of the uploaded file")
    size: int = Field(description="Size of the uploaded file, in bytes")
    type: str = Field("document", description="Always `document`")


class TextModel(ContentModel):
    text: str = Field(description="Text to summarize")
    type: str = Field("texte", description="Always `texte`")
