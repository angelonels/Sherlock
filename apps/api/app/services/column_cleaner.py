import re
from datetime import datetime
from decimal import Decimal
from typing import Any


_NON_IDENTIFIER = re.compile(r"[^a-z0-9]+")


def clean_column_names(headers: list[str]) -> list[str]:
    counts: dict[str, int] = {}
    cleaned: list[str] = []

    for index, header in enumerate(headers, start=1):
        base = _NON_IDENTIFIER.sub("_", str(header).strip().lower()).strip("_")
        if not base:
            base = f"column_{index}"
        if base[0].isdigit():
            base = f"column_{base}"

        count = counts.get(base, 0)
        counts[base] = count + 1
        cleaned.append(base if count == 0 else f"{base}_{count + 1}")

    return cleaned


def json_safe_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (datetime, Decimal)):
        return str(value)
    return str(value)


def infer_type(values: list[Any]) -> str:
    present = [value for value in values if value not in (None, "")]
    if not present:
        return "unknown"
    if all(isinstance(value, bool) for value in present):
        return "boolean"
    if all(isinstance(value, (int, float, Decimal)) and not isinstance(value, bool) for value in present):
        return "numeric"
    if all(isinstance(value, datetime) for value in present):
        return "datetime"
    return "text"


def build_detected_columns(headers: list[str], rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    cleaned = clean_column_names(headers)
    detected: list[dict[str, str]] = []

    for original_name, clean_name in zip(headers, cleaned, strict=True):
        values = [row.get(original_name) for row in rows]
        detected.append(
            {
                "original_name": original_name,
                "clean_name": clean_name,
                "inferred_type": infer_type(values),
            }
        )

    return detected
