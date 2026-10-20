from typing import Dict, Optional, Any, List, Union
from pydantic import BaseModel, ConfigDict, Field


class Text(BaseModel):
    id: str = Field(description="Identifier of this text segment")
    text: str = Field(description="The text content")
    word_count: int = Field(description="Number of words in `text`")


class PartialSummary(Text):
    text1: Text = Field(description="First of the two segments merged into this partial summary")
    text2: Text = Field(description="Second of the two segments merged into this partial summary")


class EntityModel(BaseModel):
    type: str = Field(description="Category of the entity (the name of the matching entity definition when `entity_definitions` was given, otherwise freely chosen, e.g. PERSON, DATE, ORGANIZATION)")
    text: str = Field(description="Normalized value of the entity (e.g. full name, ISO date)")
    contexts: List[str] = Field(default_factory=list, description="Sentences or phrases of the source where the entity was found")
    pages: List[int] = Field(default_factory=list, description="Page numbers where the entity appears, when known")


class RelationshipModel(BaseModel):
    source_index: int = Field(description="0-based index of the source entity in the accompanying entities list")
    target_index: int = Field(description="0-based index of the target entity in the accompanying entities list")
    relationship_type: str = Field(description="Type of the relationship between the two entities")
    description: str = Field(description="Description of the relationship, with its context")


class QAItem(BaseModel):
    page: Optional[int] = Field(None, description="Source page the question is grounded in, when known")
    source_text: str = Field(description="Passage of the source the answer is taken from")
    question: str = Field(description="Generated question")
    answer: str = Field(description="Answer to the question, grounded in `source_text`")


class TopicModel(BaseModel):
    topic: str = Field(description="General subject of the document (one of `topic_definitions` when given, otherwise freely worded)")
    confidence: float = Field(description="Confidence that this is a genuine topic of the document, between 0 and 1")
    explanation: Optional[str] = Field(None, description="Short explanation, grounded in the summary, of why the topic was assigned")


class OcrBbox(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    x: float = Field(description="Left coordinate of the box, in page pixels")
    y: float = Field(description="Top coordinate of the box, in page pixels")
    width: float = Field(description="Width of the box, in page pixels")
    height: float = Field(description="Height of the box, in page pixels")
    confidence: float = Field(description="OCR confidence for this box, between 0 and 1")
    text: str = Field(description="Text recognized in the box")
    orientation: Optional[int] = Field(None, description="Text orientation in degrees, when detected")


class OcrCheckbox(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    x: float = Field(description="Left coordinate of the checkbox, in page pixels")
    y: float = Field(description="Top coordinate of the checkbox, in page pixels")
    width: float = Field(description="Width of the checkbox, in page pixels")
    height: float = Field(description="Height of the checkbox, in page pixels")
    confidence: float = Field(description="Detection confidence, between 0 and 1")
    is_checked: bool = Field(description="Whether the checkbox is ticked")


class OcrLayout(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    cls_id: int = Field(description="Numeric id of the detected layout class")
    label: str = Field(description="Layout class label (e.g. title, table, figure)")
    score: float = Field(description="Detection score, between 0 and 1")
    coordinate: List[float] = Field(description="Bounding box of the layout element as a list of coordinates")
    content: Optional[Any] = Field(None, description="Content extracted from the element, when available")


class OcrPage(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    page: int = Field(description="1-based page number")
    page_url: Optional[str] = Field(None, description="URL of the rendered page image, when available")
    boxes: List[OcrBbox] = Field(default_factory=list, description="Text boxes recognized on the page")
    checkboxes: List[OcrCheckbox] = Field(default_factory=list, description="Checkboxes detected on the page")
    layouts: List[OcrLayout] = Field(default_factory=list, description="Layout elements detected on the page")
    page_markdown: Optional[str] = Field(None, description="Markdown rendering of the page, when available")


class ResultModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    type: str = Field(description="Kind of result")
    created_at: int = Field(description="Creation time, Unix timestamp (seconds)")
    model_name: str = Field(description="Name of the LLM that produced the result")
    model_version: str = Field(description="Version of the LLM that produced the result")
    updated_at: Optional[int] = Field(None, description="Last update time, Unix timestamp (seconds)")
    texts_found: Optional[List[str]] = Field(default_factory=list, description="Source text extracted from the input, split in pages or sections (empty unless `show_text_found=true`)")
    ocr_pages: Optional[List[OcrPage]] = Field(default_factory=list, description="OCR details per page, for scanned documents and images")
    percentage: float = Field(0.0, description="Progress of the task, between 0 and 1")
    extras: Optional[Dict[str, Any]] = Field(None, description="Free-form extra information")
    partial_summaries: Optional[List[Union[PartialSummary, Text]]] = Field(default_factory=list, description="Intermediate summaries built while merging the document (map-reduce)")
    qa_items: Optional[List[QAItem]] = Field(default_factory=list, description="Question/answer pairs, when `extract_qa` was requested")


class SummaryModel(ResultModel):
    summary: str = Field(description="The generated summary, in Markdown")
    word_count: int = Field(description="Number of words in `summary`")
    nb_llm_calls: Optional[int] = Field(0, description="Number of LLM calls spent producing the summary")
    type: str = Field("summary", description="Always `summary`")
    entities: List[EntityModel] = Field(default_factory=list, description="Entities found, when `extract_entities` was requested")
    relationships: List[RelationshipModel] = Field(default_factory=list, description="Relationships between the entities, when `extract_entities` was requested")
