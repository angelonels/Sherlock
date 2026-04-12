from datetime import datetime
from pydantic import BaseModel


class UploadSessionResponse(BaseModel):
    id: str
    original_filename: str
    file_extension: str
    file_size_bytes: int
    status: str
    sheet_names: list[str] | None = None
    selected_sheet_name: str | None = None
    preview_rows: list[dict] | None = None
    detected_columns: list[dict] | None = None
    warnings: list[dict] | list[str] = []
    expires_at: datetime

    class Config:
        from_attributes = True


class DatasetCreate(BaseModel):
    upload_session_id: str
    name: str
    selected_sheet_name: str | None = None


class DatasetResponse(BaseModel):
    id: str
    name: str
    original_filename: str | None = None
    source_file_type: str
    selected_sheet_name: str | None = None
    status: str
    original_row_count: int
    row_count: int
    duplicate_rows_removed: int
    column_count: int
    total_missing_values: int
    quality_status: str | None = None
    quality_score: float | None = None
    created_at: datetime
    updated_at: datetime | None = None
    locked_at: datetime | None = None

    class Config:
        from_attributes = True
