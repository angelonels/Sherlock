import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class UploadDetectedColumn(BaseModel):
    original_name: str
    clean_name: str
    inferred_type: str


class UploadWarning(BaseModel):
    code: str
    message: str
    severity: str = "warning"


class UploadSessionRead(BaseModel):
    id: uuid.UUID
    original_filename: str
    file_extension: str
    file_size_bytes: int
    status: str
    sheet_names: list[str] | None = None
    selected_sheet_name: str | None = None
    recommended_sheet_name: str | None = None
    preview_rows: list[dict[str, Any]]
    detected_columns: list[UploadDetectedColumn]
    warnings: list[UploadWarning]
    expires_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UploadSessionUpdate(BaseModel):
    selected_sheet_name: str | None = None
