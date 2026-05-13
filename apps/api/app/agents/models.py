from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class QueryPlan(BaseModel):
    step_index: int = 1
    purpose: str
    sql: str


class DatasetContext(BaseModel):
    id: str
    name: str
    physical_schema_name: str
    physical_table_name: str
    row_count: int
    column_count: int
    quality_status: str | None = None


class DatasetColumnContext(BaseModel):
    column_name: str
    original_column_name: str
    column_index: int
    postgres_type: str
    pandas_type: str | None = None
    semantic_type: str
    nullable_count: int = 0
    nullable_ratio: float = 0
    distinct_count: int | None = None
    sample_values: list[Any] | None = None
    min_value: str | None = None
    max_value: str | None = None
    warning_flags: list[str] = Field(default_factory=list)


class DatasetQualityIssueContext(BaseModel):
    issue_type: str
    severity: str
    title: str
    description: str
    affected_row_count: int | None = None
    affected_ratio: float | None = None
    sample_values: list[Any] | None = None


class QueryFailure(BaseModel):
    step_index: int
    error: str
    sql: str | None = None


class QueryResultSummary(BaseModel):
    step_index: int
    purpose: str
    status: Literal["success", "failed"]
    sql: str | None = None
    columns: list[str] = Field(default_factory=list)
    rows: list[dict[str, Any]] = Field(default_factory=list)
    row_count: int = 0
    error: str | None = None


class IntentResult(BaseModel):
    intent: Literal["data_question", "schema_question", "quality_question", "summary_question", "unsupported_question"]


class AnalysisPlan(BaseModel):
    intent: str
    query_plans: list[QueryPlan] = Field(default_factory=list)


class AnswerSynthesis(BaseModel):
    content: str
    blocks: list[dict[str, Any]] = Field(default_factory=list)
