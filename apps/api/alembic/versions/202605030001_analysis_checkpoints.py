"""Add analysis checkpoints.

Revision ID: 202605030001
Revises: 202605020001
Create Date: 2026-05-03 01:40:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "202605030001"
down_revision: str | None = "202605020001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "analysis_checkpoints",
        sa.Column("thread_id", sa.Text(), nullable=False),
        sa.Column("checkpoint_ns", sa.Text(), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("thread_id", "checkpoint_ns", name="pk_analysis_checkpoints"),
    )


def downgrade() -> None:
    op.drop_table("analysis_checkpoints")
