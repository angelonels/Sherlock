from __future__ import annotations

import re
from typing import Any

import pandas as pd


PII_COLUMN_HINTS = {
    "email",
    "e_mail",
    "phone",
    "mobile",
    "ssn",
    "social_security",
    "passport",
    "dob",
    "date_of_birth",
    "address",
}
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^\+?[\d\s().-]{7,}$")
SSN_RE = re.compile(r"^\d{3}-\d{2}-\d{4}$")


def pii_warning_flags(profile: dict[str, Any]) -> list[str]:
    column_name = str(profile["column_name"]).lower()
    original_name = str(profile["original_column_name"]).lower()
    flags: list[str] = []
    if any(hint in column_name or hint in original_name for hint in PII_COLUMN_HINTS):
        flags.append("pii_like_column_name")

    samples = [str(value).strip() for value in profile.get("sample_values") or [] if value is not None]
    if any(EMAIL_RE.match(value) for value in samples):
        flags.append("pii_like_email_values")
    if any(PHONE_RE.match(value) for value in samples):
        flags.append("pii_like_phone_values")
    if any(SSN_RE.match(value) for value in samples):
        flags.append("pii_like_ssn_values")
    return list(dict.fromkeys(flags))


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
        pii_flags = pii_warning_flags(profile)
        if pii_flags:
            warning_flags = list(dict.fromkeys([*profile.get("warning_flags", []), *pii_flags]))
            profile["warning_flags"] = warning_flags
            issues.append(
                {
                    "issue_type": "pii_like_values_detected",
                    "severity": "warning",
                    "title": f"PII-like values detected in {profile['column_name']}",
                    "description": (
                        f"{profile['column_name']} looks like it may contain personal data. "
                        "Sherlock will allow analysis, but answers should be reviewed carefully before sharing."
                    ),
                    "affected_row_count": None,
                    "affected_ratio": None,
                    "sample_values": profile.get("sample_values"),
                }
            )
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
