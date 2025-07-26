from typing import Dict, Optional, Any, List, Union
from pydantic import BaseModel, ConfigDict


class ResultModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    type: str
    created_at: int
    model_name: str
    model_version: str
    updated_at: Optional[int] = None
    texts_found: Optional[List[str]] = []
    percentage: float = 0.0
    extras: Optional[Dict[str, Any]] = None


class Text(BaseModel):
    id: str
    text: str
    word_count: int


class PartialSummary(Text):
    text1: Text
    text2: Text


class SummaryModel(ResultModel):
    summary: str
    word_count: int
    nb_llm_calls: Optional[int] = 0
    type: str = "summary"
    partial_summaries: Optional[List[Union[PartialSummary, Text]]] = []
