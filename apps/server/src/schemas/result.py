from typing import Dict, Optional, Any, List, Union
from pydantic import BaseModel, ConfigDict


class Text(BaseModel):
    id: str
    text: str
    word_count: int


class PartialSummary(Text):
    text1: Text
    text2: Text


class EntityModel(BaseModel):
    type: str
    text: str
    contexts: List[str] = []
    pages: List[int] = []


class RelationshipModel(BaseModel):
    source_index: int
    target_index: int
    relationship_type: str
    description: str


class QAItem(BaseModel):
    page: Optional[int] = None
    source_text: str
    question: str
    answer: str


class OcrBbox(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    x: float
    y: float
    width: float
    height: float
    confidence: float
    text: str
    orientation: Optional[int] = None


class OcrCheckbox(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    x: float
    y: float
    width: float
    height: float
    confidence: float
    is_checked: bool


class OcrLayout(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    cls_id: int
    label: str
    score: float
    coordinate: List[float]
    content: Optional[Any] = None


class OcrPage(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    page: int
    page_url: Optional[str] = None
    boxes: List[OcrBbox] = []
    checkboxes: List[OcrCheckbox] = []
    layouts: List[OcrLayout] = []
    page_markdown: Optional[str] = None


class ResultModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    type: str
    created_at: int
    model_name: str
    model_version: str
    updated_at: Optional[int] = None
    texts_found: Optional[List[str]] = []
    ocr_pages: Optional[List[OcrPage]] = []
    percentage: float = 0.0
    extras: Optional[Dict[str, Any]] = None
    partial_summaries: Optional[List[Union[PartialSummary, Text]]] = []
    qa_items: Optional[List[QAItem]] = []


class SummaryModel(ResultModel):
    summary: str
    word_count: int
    nb_llm_calls: Optional[int] = 0
    type: str = "summary"
    entities: List[EntityModel] = []
    relationships: List[RelationshipModel] = []
