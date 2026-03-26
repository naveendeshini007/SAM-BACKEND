from pydantic import BaseModel, Field
from typing import Generic, TypeVar, List

T = TypeVar("T")

class PaginationParams(BaseModel):
    page: int = Field(1, ge=1, description="Page number")
    limit: int = Field(10, ge=1, le=100, description="Items per page")


class PaginatedResponse(BaseModel, Generic[T]):
    total: int
    page: int
    limit: int
    total_pages: int
    data: List[T]