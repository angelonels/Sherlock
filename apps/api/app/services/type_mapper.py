from __future__ import annotations

import pandas as pd


def postgres_type_for_series(series: pd.Series) -> str:
    if pd.api.types.is_bool_dtype(series):
        return "BOOLEAN"
    if pd.api.types.is_integer_dtype(series):
        return "BIGINT"
    if pd.api.types.is_float_dtype(series):
        return "DOUBLE PRECISION"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "TIMESTAMPTZ"
    return "TEXT"


def semantic_type_for_series(name: str, series: pd.Series) -> str:
    lowered = name.lower()
    if lowered.endswith("_id") or lowered == "id":
        return "identifier"
    if pd.api.types.is_datetime64_any_dtype(series) or "date" in lowered or "time" in lowered:
        return "datetime"
    if pd.api.types.is_numeric_dtype(series):
        return "numeric"
    if pd.api.types.is_bool_dtype(series):
        return "boolean"
    unique_count = series.dropna().nunique()
    if unique_count and unique_count <= max(20, int(len(series) * 0.2)):
        return "category"
    return "text"
