from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


ChartType = Literal[
    "kpi",
    "line",
    "bar",
    "horizontal_bar",
    "stacked_bar",
    "area",
    "pie",
    "donut",
    "scatter",
    "histogram",
]


class ChartSpec(BaseModel):
    type: ChartType
    title: str
    x_key: str | None = None
    y_key: str | None = None
    series_key: str | None = None
    value_key: str | None = None
    label_key: str | None = None
    data: list[dict[str, Any]] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)


class ChartService:
    def __init__(self, max_chart_rows: int = 500) -> None:
        self.max_chart_rows = max_chart_rows

    def recommend(self, rows: list[dict[str, Any]], *, title: str = "Chart") -> ChartSpec | None:
        capped = rows[: self.max_chart_rows]
        if not capped:
            return None

        keys = list(capped[0].keys())
        numeric_keys = [key for key in keys if self._is_numeric_series(capped, key)]
        date_keys = [key for key in keys if self._is_date_key(key) or self._is_date_series(capped, key)]
        category_keys = [key for key in keys if key not in numeric_keys and key not in date_keys]

        if len(capped) == 1 and numeric_keys:
            key = numeric_keys[0]
            return ChartSpec(type="kpi", title=title, value_key=key, data=[{key: capped[0].get(key)}])
        if len(numeric_keys) == 1 and len(keys) == 1:
            return self.histogram(capped, numeric_keys[0], title=title)
        if len(numeric_keys) >= 2 and not category_keys and not date_keys:
            return ChartSpec(type="scatter", title=title, x_key=numeric_keys[0], y_key=numeric_keys[1], data=capped)
        if date_keys and numeric_keys:
            chart_type: ChartType = "area" if any("volume" in key.lower() or "count" in key.lower() for key in numeric_keys) else "line"
            return ChartSpec(type=chart_type, title=title, x_key=date_keys[0], y_key=numeric_keys[0], data=capped)
        if category_keys and numeric_keys and len(category_keys) >= 2:
            return ChartSpec(type="stacked_bar", title=title, x_key=category_keys[0], y_key=numeric_keys[0], series_key=category_keys[1], data=capped)
        if category_keys and numeric_keys:
            chart_type = "horizontal_bar" if self._has_long_labels(capped, category_keys[0]) or len(capped) > 8 else "bar"
            return ChartSpec(type=chart_type, title=title, x_key=category_keys[0], y_key=numeric_keys[0], data=capped)
        return None

    def pie_or_donut(self, rows: list[dict[str, Any]], *, title: str = "Share", donut: bool = True) -> ChartSpec | None:
        capped = rows[: self.max_chart_rows]
        if not capped or len(capped) > 8:
            return None
        keys = list(capped[0].keys())
        numeric_keys = [key for key in keys if self._is_numeric_series(capped, key)]
        label_keys = [key for key in keys if key not in numeric_keys]
        if not numeric_keys or not label_keys:
            return None
        return ChartSpec(
            type="donut" if donut else "pie",
            title=title,
            label_key=label_keys[0],
            value_key=numeric_keys[0],
            data=capped,
        )

    def histogram(self, rows: list[dict[str, Any]], key: str, *, title: str = "Distribution", bins: int = 10) -> ChartSpec:
        values = sorted(float(row[key]) for row in rows if self._is_number(row.get(key)))
        if not values:
            return ChartSpec(type="histogram", title=title, x_key="bin", y_key="count", data=[])
        low, high = values[0], values[-1]
        width = (high - low) / bins if high != low else 1
        bucket_rows: list[dict[str, Any]] = []
        for index in range(bins):
            start = low + index * width
            end = start + width
            count = sum(1 for value in values if start <= value < end or (index == bins - 1 and value == high))
            bucket_rows.append({"bin": f"{start:.2f}-{end:.2f}", "count": count})
        return ChartSpec(type="histogram", title=title, x_key="bin", y_key="count", data=bucket_rows)

    def chart_block(self, spec: ChartSpec) -> dict[str, Any]:
        return {"type": "chart", "spec": spec.model_dump()}

    def _is_number(self, value: Any) -> bool:
        return isinstance(value, (int, float)) and not isinstance(value, bool)

    def _is_numeric_series(self, rows: list[dict[str, Any]], key: str) -> bool:
        values = [row.get(key) for row in rows if row.get(key) is not None]
        return bool(values) and all(self._is_number(value) for value in values)

    def _is_date_key(self, key: str) -> bool:
        lowered = key.lower()
        return "date" in lowered or "month" in lowered or "time" in lowered

    def _is_date_series(self, rows: list[dict[str, Any]], key: str) -> bool:
        values = [row.get(key) for row in rows if row.get(key) is not None]
        return bool(values) and all(isinstance(value, (date, datetime)) for value in values)

    def _has_long_labels(self, rows: list[dict[str, Any]], key: str) -> bool:
        return any(len(str(row.get(key, ""))) > 16 for row in rows)
