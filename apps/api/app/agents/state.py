from typing import Any, TypedDict


class AnalystState(TypedDict, total=False):
    analysis_run_id: str
    chat_id: str
    dataset_id: str
    user_question: str
    intent: str
    query_results: list[dict[str, Any]]
    query_failures: list[dict[str, Any]]
    answer: str
    blocks: list[dict[str, Any]]
