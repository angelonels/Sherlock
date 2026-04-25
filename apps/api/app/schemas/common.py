from typing import Generic, TypeVar

from pydantic import BaseModel


DataT = TypeVar("DataT")


class DataEnvelope(BaseModel, Generic[DataT]):
    data: DataT


class Pagination(BaseModel):
    next_cursor: str | None = None


class ListEnvelope(BaseModel, Generic[DataT]):
    data: list[DataT]
    pagination: Pagination = Pagination()


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: object | None = None
    request_id: str | None = None


class ErrorEnvelope(BaseModel):
    error: ErrorDetail
