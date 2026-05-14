from __future__ import annotations

from typing import Any, TypedDict

from app.agents.models import DatasetColumnContext, DatasetContext, DatasetQualityIssueContext, QueryPlan, QueryResultSummary


class AnalystState(TypedDict, total=False):
    analysis_run_id: str
    chat_id: str
    dataset_id: str
    user_question: str
    user_message_id: str
    memory_summary: str | None
    dataset: DatasetContext
    columns: list[DatasetColumnContext]
    quality_issues: list[DatasetQualityIssueContext]
    intent: str
    query_plans: list[QueryPlan]
    query_results: list[QueryResultSummary]
    query_failures: list[QueryResultSummary]
    content: str
    blocks: list[dict[str, Any]]
    assistant_message_id: str
