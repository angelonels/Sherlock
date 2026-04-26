from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any

from fastapi import status

from app.core.config import Settings
from app.core.errors import ApiError


SUPPORTED_EXTENSIONS = {"csv", "xlsx"}
FORMULA_PREFIXES = ("=", "+", "-", "@")


def upload_error(code: str, message: str, details: Any = None) -> ApiError:
    return ApiError(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, code=code, message=message, details=details)


def validate_extension(filename: str) -> str:
    suffix = Path(filename).suffix.lower().lstrip(".")
    if suffix == "xlsm":
        raise upload_error("UNSUPPORTED_UPLOAD_TYPE", "Macro-enabled Excel files are not supported.")
    if suffix not in SUPPORTED_EXTENSIONS:
        raise upload_error("UNSUPPORTED_UPLOAD_TYPE", "Only CSV and XLSX files are supported.")
    return suffix


def validate_file_size(size: int, settings: Settings) -> None:
    if size == 0:
        raise upload_error("EMPTY_UPLOAD", "Uploaded file is empty.")
    if size > settings.upload_max_file_size_bytes:
        raise upload_error(
            "UPLOAD_TOO_LARGE",
            "Uploaded file exceeds the configured size limit.",
            {"max_file_size_bytes": settings.upload_max_file_size_bytes},
        )


def validate_cell_width(value: Any, settings: Settings) -> None:
    if isinstance(value, str) and len(value) > settings.upload_max_cell_length:
        raise upload_error(
            "CELL_TOO_WIDE",
            "Uploaded file contains a cell that exceeds the configured length limit.",
            {"max_cell_length": settings.upload_max_cell_length},
        )


def is_formula_like(value: Any) -> bool:
    return isinstance(value, str) and value.startswith(FORMULA_PREFIXES)


def build_warning(code: str, message: str, severity: str = "warning") -> dict[str, str]:
    return {"code": code, "message": message, "severity": severity}


def warning_for_rows(rows: list[dict[str, Any]], settings: Settings) -> list[dict[str, str]]:
    found_formula = False
    for row in rows:
        for value in row.values():
            validate_cell_width(value, settings)
            if is_formula_like(value):
                found_formula = True

    if found_formula:
        return [
            build_warning(
                "FORMULA_LIKE_VALUES_DETECTED",
                "Some cells look like spreadsheet formulas and will be stored as inert text.",
            )
        ]
    return []


def build_temp_file_key(user_id: uuid.UUID, extension: str) -> str:
    return f"{user_id.hex}/{uuid.uuid4().hex}.{extension}"


def temp_file_path(settings: Settings, temp_file_key: str) -> Path:
    root = Path(settings.upload_tmp_dir).resolve()
    path = (root / temp_file_key).resolve()
    if os.path.commonpath([root, path]) != str(root):
        raise ApiError(status_code=status.HTTP_400_BAD_REQUEST, code="INVALID_TEMP_FILE_KEY", message="Invalid temp file key.")
    return path


def write_temp_file(settings: Settings, temp_file_key: str, content: bytes) -> None:
    path = temp_file_path(settings, temp_file_key)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def read_temp_file(settings: Settings, temp_file_key: str) -> bytes:
    path = temp_file_path(settings, temp_file_key)
    if not path.exists():
        raise ApiError(status_code=status.HTTP_410_GONE, code="UPLOAD_FILE_MISSING", message="Upload file is no longer available.")
    return path.read_bytes()


def delete_temp_file(settings: Settings, temp_file_key: str) -> None:
    temp_file_path(settings, temp_file_key).unlink(missing_ok=True)
