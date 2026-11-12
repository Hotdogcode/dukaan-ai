"""
Common API Schemas and Standard Response Formats for DukaanAI.
"""

from typing import Any, Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """Structured detail item within an error response."""
    code: str
    message: str
    request_id: str | None = None
    details: list[dict[str, Any]] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    """Standardized top-level API error envelope."""
    error: ErrorDetail


class MessageResponse(BaseModel):
    """Simple confirmation response message."""
    message: str


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard pagination envelope."""
    items: list[T]
    total_count: int
    limit: int
    offset: int
