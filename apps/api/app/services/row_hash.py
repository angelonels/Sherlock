from __future__ import annotations

import hashlib
import json
from typing import Any

import pandas as pd


def row_hash(row: pd.Series) -> str:
    payload: dict[str, Any] = {str(key): _json_safe(value) for key, value in row.items()}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


def _json_safe(value: Any) -> Any:
    if pd.isna(value):
        return None
    return value
