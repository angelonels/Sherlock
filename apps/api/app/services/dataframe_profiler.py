from __future__ import annotations

from typing import Any

import pandas as pd

from app.services.type_mapper import postgres_type_for_series, semantic_type_for_series


def json_sample(values: list[Any]) -> list[Any]:
    cleaned: list[Any] = []
    for value in values:
        if pd.isna(value):
            continue
        cleaned.append(value.item() if hasattr(value, "item") else value)
        if len(cleaned) >= 5:
            break
    return cleaned


def profile_columns(frame: pd.DataFrame, original_names: dict[str, str]) -> list[dict[str, Any]]:
    total = max(len(frame), 1)
    profiles: list[dict[str, Any]] = []
    for index, column_name in enumerate(frame.columns):
        series = frame[column_name]
        nullable_count = int(series.isna().sum())
        profiles.append(
            {
                "column_index": index,
                "column_name": column_name,
                "original_column_name": original_names.get(column_name, column_name),
                "postgres_type": postgres_type_for_series(series),
                "pandas_type": str(series.dtype),
                "semantic_type": semantic_type_for_series(column_name, series),
                "nullable_count": nullable_count,
                "nullable_ratio": nullable_count / total,
                "distinct_count": int(series.dropna().nunique()),
                "sample_values": json_sample(series.dropna().head(20).tolist()),
                "min_value": str(series.min()) if len(series.dropna()) else None,
                "max_value": str(series.max()) if len(series.dropna()) else None,
                "warning_flags": [],
            }
        )
    return profiles
