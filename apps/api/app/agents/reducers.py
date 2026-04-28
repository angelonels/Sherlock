from typing import Any


def append_query_results(existing: list[dict[str, Any]] | None, new: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    return [*(existing or []), *(new or [])]


def append_query_failures(existing: list[dict[str, Any]] | None, new: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    return [*(existing or []), *(new or [])]
