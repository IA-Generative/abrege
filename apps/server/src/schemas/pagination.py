from pydantic import BaseModel, Field
from typing import Generic, TypeVar, Optional

T = TypeVar("T", bound=BaseModel)


class Pagination(BaseModel, Generic[T]):
    total: int = Field(description="Total number of items across all pages")
    page: int = Field(description="Current page number (1-based)")
    page_size: int = Field(description="Maximum number of items per page")
    items: Optional[list[T]] = Field(None, description="Items of the current page")
