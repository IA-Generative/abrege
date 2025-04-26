from typing import Dict, Optional, Any
from pydantic import BaseModel, ConfigDict


class ContentModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    type: str
    created_at: int
    extras: Optional[Dict[str, Any]] = None


class URLModel(ContentModel):
    url: str
    type: str = "url"


class DocumentModel(ContentModel):
    file_path: str
    raw_filename: str
    content_type: str
    ext: str
    type: str = "document"


class TextModel(ContentModel):
    text: str
    type: str = "texte"
