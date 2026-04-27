from __future__ import annotations

from typing import Any

import pandas as pd


def build_quality_issues(
    frame: pd.DataFrame,
    *,
    duplicate_rows_removed: int,
    column_profiles: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    if duplicate_rows_removed:
        issues.append(
            {
                "issue_type": "exact_duplicates_removed",
                "severity": "info",
                "title": "Exact duplicate rows removed",
                "description": f"{duplicate_rows_removed} exact duplicate rows were removed during ingestion.",
                "affected_row_count": duplicate_rows_removed,
                "affected_ratio": None,
                "sample_values": None,
            }
        )

    for profile in column_profiles:
        if profile["nullable_count"] > 0:
            issue_type = "high_missing_ratio" if profile["nullable_ratio"] >= 0.4 else "missing_values"
            issues.append(
                {
                    "issue_type": issue_type,
                    "severity": "warning" if issue_type == "high_missing_ratio" else "info",
                    "title": f"Missing values in {profile['column_name']}",
                    "description": f"{profile['nullable_count']} rows are missing values for {profile['column_name']}.",
                    "affected_row_count": profile["nullable_count"],
                    "affected_ratio": profile["nullable_ratio"],
                    "sample_values": None,
                }
            )

    return issues


def quality_status(issues: list[dict[str, Any]]) -> tuple[str, float]:
    critical = sum(1 for issue in issues if issue["severity"] == "critical")
    warnings = sum(1 for issue in issues if issue["severity"] == "warning")
    if critical:
        return "poor", 40.0
    if warnings:
        return "warning", 76.0
    return "good", 95.0
