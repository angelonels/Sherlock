import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DatasetCreate(BaseModel):
    upload_session_id: uuid.UUID
    name: str
    selected_sheet_name: str | None = None


class DatasetRead(BaseModel):
    id: uuid.UUID
    name: str
    status: str
    source_file_type: str
    selected_sheet_name: str | None = None
    original_filename: str | None = None
    row_count: int = 0
    original_row_count: int = 0
    duplicate_rows_removed: int = 0
    column_count: int = 0
    total_missing_values: int = 0
    quality_status: str | None = None
    quality_score: float | None = None
    ingestion_error: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DatasetColumnRead(BaseModel):
    id: uuid.UUID
    column_index: int
    column_name: str
    original_column_name: str
    postgres_type: str
    pandas_type: str | None = None
    semantic_type: str
    nullable_count: int = 0
    nullable_ratio: float = 0
    distinct_count: int | None = None
    sample_values: list[Any] | None = None
    warning_flags: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class DatasetQualityIssueRead(BaseModel):
    id: uuid.UUID
    issue_type: str
    severity: str
    title: str
    description: str
    affected_row_count: int | None = None
    affected_ratio: float | None = None
    sample_values: list[Any] | None = None

    model_config = ConfigDict(from_attributes=True)


class DatasetPreviewRead(BaseModel):
    rows: list[dict[str, Any]]
    columns: list[str]
