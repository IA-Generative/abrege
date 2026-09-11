from pydantic import BaseModel
from typing import Generic, TypeVar, Optional

T = TypeVar("T", bound=BaseModel)


class Pagination(BaseModel, Generic[T]):
    total: int
    page: int
    page_size: int
    items: Optional[list[T]] = None
