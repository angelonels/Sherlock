from __future__ import annotations

import pandas as pd


MISSING_MARKERS = {"", " ", "na", "n/a", "null", "none", "nan", "-", "--"}


def normalize_missing_values(frame: pd.DataFrame) -> pd.DataFrame:
    normalized = frame.copy()
    for column in normalized.columns:
        if normalized[column].dtype == object:
            normalized[column] = normalized[column].map(
                lambda value: None if isinstance(value, str) and value.strip().lower() in MISSING_MARKERS else value
            )
    return normalized.where(pd.notnull(normalized), None)
