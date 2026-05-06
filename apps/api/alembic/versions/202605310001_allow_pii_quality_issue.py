"""Allow PII-like quality warnings.

Revision ID: 202605310001
Revises: 202605030001
Create Date: 2026-05-31 02:05:00.000000
"""

from collections.abc import Sequence

from alembic import op


revision: str = "202605310001"
down_revision: str | None = "202605030001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


ISSUE_TYPES_WITH_PII = (
    "'missing_values', 'exact_duplicates_removed', 'high_missing_ratio', 'mostly_empty_column', "
    "'constant_column', 'high_cardinality_text', 'mixed_type_values', 'date_parse_failures', "
    "'numeric_parse_failures', 'formula_like_values_detected', 'wide_cells_detected', "
    "'pii_like_values_detected'"
)

ISSUE_TYPES_WITHOUT_PII = (
    "'missing_values', 'exact_duplicates_removed', 'high_missing_ratio', 'mostly_empty_column', "
    "'constant_column', 'high_cardinality_text', 'mixed_type_values', 'date_parse_failures', "
    "'numeric_parse_failures', 'formula_like_values_detected', 'wide_cells_detected'"
)


def upgrade() -> None:
    op.drop_constraint("ck_dataset_quality_issues_issue_type", "dataset_quality_issues", type_="check")
    op.create_check_constraint(
        "ck_dataset_quality_issues_issue_type",
        "dataset_quality_issues",
        f"issue_type IN ({ISSUE_TYPES_WITH_PII})",
    )


def downgrade() -> None:
    op.drop_constraint("ck_dataset_quality_issues_issue_type", "dataset_quality_issues", type_="check")
    op.create_check_constraint(
        "ck_dataset_quality_issues_issue_type",
        "dataset_quality_issues",
        f"issue_type IN ({ISSUE_TYPES_WITHOUT_PII})",
    )
