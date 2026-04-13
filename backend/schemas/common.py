from typing import Generic, TypeVar
from pydantic import BaseModel, Field


T = TypeVar("T")


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict | None = None
    request_id: str | None = None


class ErrorEnvelope(BaseModel):
    error: ErrorBody


class Pagination(BaseModel):
    next_cursor: str | None = None


class ResourceEnvelope(BaseModel, Generic[T]):
    data: T
    links: dict[str, str] | None = None


class ListEnvelope(BaseModel, Generic[T]):
    data: list[T]
    pagination: Pagination = Field(default_factory=Pagination)
