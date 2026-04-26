from __future__ import annotations

import csv
from io import StringIO
from typing import Any

from app.core.config import Settings
from app.services.column_cleaner import build_detected_columns, json_safe_value
from app.services.upload_safety import upload_error, warning_for_rows


def detect_encoding(content: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8"):
        try:
            content.decode(encoding)
            return encoding
        except UnicodeDecodeError:
            continue
    return "latin-1"


def detect_delimiter(text: str) -> str:
    sample = text[:8192]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        return dialect.delimiter
    except csv.Error:
        return ","


def inspect_csv(content: bytes, settings: Settings) -> dict[str, Any]:
    if b"\x00" in content:
        raise upload_error("INVALID_CSV", "CSV file contains null bytes.")

    encoding = detect_encoding(content)
    text = content.decode(encoding)
    if not text.strip():
        raise upload_error("EMPTY_UPLOAD", "Uploaded CSV is empty.")

    delimiter = detect_delimiter(text)
    reader = csv.reader(StringIO(text), delimiter=delimiter)
    rows = list(reader)
    if not rows or not any(cell.strip() for cell in rows[0]):
        raise upload_error("EMPTY_UPLOAD", "Uploaded CSV does not contain headers.")

    headers = [header.strip() or f"Column {index}" for index, header in enumerate(rows[0], start=1)]
    if len(headers) > settings.upload_max_columns:
        raise upload_error("TOO_MANY_COLUMNS", "Uploaded file has too many columns.", {"max_columns": settings.upload_max_columns})

    data_rows = rows[1:]
    if not any(any(cell.strip() for cell in row) for row in data_rows):
        raise upload_error("HEADERS_ONLY_UPLOAD", "Uploaded CSV contains headers but no data rows.")

    preview_rows: list[dict[str, Any]] = []
    for row_number, row in enumerate(data_rows, start=2):
        if len(row) != len(headers):
            raise upload_error(
                "MALFORMED_CSV",
                "CSV contains a row with a different column count than the header row.",
                {"row_number": row_number},
            )
        if not any(cell.strip() for cell in row):
            continue
        preview_rows.append({header: json_safe_value(value) for header, value in zip(headers, row, strict=True)})
        if len(preview_rows) >= settings.upload_preview_rows:
            break

    warnings = warning_for_rows(preview_rows, settings)
    warnings.append({"code": "CSV_FORMAT_DETECTED", "message": f"Detected {encoding} encoding and {delimiter!r} delimiter.", "severity": "info"})

    return {
        "sheet_names": None,
        "selected_sheet_name": None,
        "recommended_sheet_name": None,
        "preview_rows": preview_rows,
        "detected_columns": build_detected_columns(headers, preview_rows),
        "warnings": warnings,
    }
