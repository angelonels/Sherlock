from __future__ import annotations

import pandas as pd


def drop_exact_duplicates(frame: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    before = len(frame)
    deduped = frame.drop_duplicates().reset_index(drop=True)
    return deduped, before - len(deduped)
