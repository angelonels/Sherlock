from __future__ import annotations

import pandas as pd

from app.services.dataframe_profiler import profile_columns
from app.services.quality_service import build_quality_issues


def test_pii_like_email_column_warns_without_blocking() -> None:
    frame = pd.DataFrame(
        {
            "email": ["customer@example.com", "ops@example.com"],
            "revenue": [100, 200],
        }
    )
    profiles = profile_columns(frame, {"email": "Email", "revenue": "Revenue"})

    issues = build_quality_issues(frame, duplicate_rows_removed=0, column_profiles=profiles)

    assert any(issue["issue_type"] == "pii_like_values_detected" for issue in issues)
    email_profile = next(profile for profile in profiles if profile["column_name"] == "email")
    assert "pii_like_column_name" in email_profile["warning_flags"]
    assert "pii_like_email_values" in email_profile["warning_flags"]
