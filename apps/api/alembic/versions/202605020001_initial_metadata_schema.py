"""Initial production metadata schema.

Revision ID: 202605020001
Revises:
Create Date: 2026-05-02 00:01:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "202605020001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE SCHEMA IF NOT EXISTS user_data")

    op.create_table(
        "app_users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("clerk_user_id", sa.Text(), nullable=False),
        sa.Column("email", sa.Text(), nullable=True),
        sa.Column("first_name", sa.Text(), nullable=True),
        sa.Column("last_name", sa.Text(), nullable=True),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("clerk_user_id", name="uq_app_users_clerk_user_id"),
    )
    op.create_index("idx_app_users_clerk_user_id", "app_users", ["clerk_user_id"], unique=True)

    op.create_table(
        "upload_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("original_filename", sa.Text(), nullable=False),
        sa.Column("file_extension", sa.Text(), nullable=False),
        sa.Column("temp_file_key", sa.Text(), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("sheet_names", postgresql.JSONB(), nullable=True),
        sa.Column("selected_sheet_name", sa.Text(), nullable=True),
        sa.Column("preview_rows", postgresql.JSONB(), nullable=True),
        sa.Column("detected_columns", postgresql.JSONB(), nullable=True),
        sa.Column("warnings", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("file_extension IN ('csv', 'xlsx')", name="ck_upload_sessions_file_extension"),
        sa.CheckConstraint(
            "status IN ('uploaded', 'inspected', 'ingested', 'expired', 'failed', 'deleted')",
            name="ck_upload_sessions_status",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["app_users.id"], name="fk_upload_sessions_user_id", ondelete="CASCADE"),
    )
    op.create_index("idx_upload_sessions_user_status", "upload_sessions", ["user_id", "status"])
    op.create_index("idx_upload_sessions_expires_at", "upload_sessions", ["expires_at"])

    op.create_table(
        "datasets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("upload_session_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("original_filename", sa.Text(), nullable=True),
        sa.Column("source_file_type", sa.Text(), nullable=False),
        sa.Column("selected_sheet_name", sa.Text(), nullable=True),
        sa.Column("physical_schema_name", sa.Text(), nullable=False, server_default=sa.text("'user_data'")),
        sa.Column("physical_table_name", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("original_row_count", sa.BigInteger(), nullable=False, server_default=sa.text("0")),
        sa.Column("row_count", sa.BigInteger(), nullable=False, server_default=sa.text("0")),
        sa.Column("duplicate_rows_removed", sa.BigInteger(), nullable=False, server_default=sa.text("0")),
        sa.Column("column_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("total_missing_values", sa.BigInteger(), nullable=False, server_default=sa.text("0")),
        sa.Column("quality_status", sa.Text(), nullable=True),
        sa.Column("quality_score", sa.Double(), nullable=True),
        sa.Column("ingestion_error", sa.Text(), nullable=True),
        sa.Column("raw_file_deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("physical_table_dropped_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("source_file_type IN ('csv', 'xlsx')", name="ck_datasets_source_file_type"),
        sa.CheckConstraint(
            "status IN ('processing', 'ready', 'locked', 'failed', 'deleted')",
            name="ck_datasets_status",
        ),
        sa.CheckConstraint(
            "quality_status IS NULL OR quality_status IN ('good', 'warning', 'poor')",
            name="ck_datasets_quality_status",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["app_users.id"], name="fk_datasets_user_id", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["upload_session_id"],
            ["upload_sessions.id"],
            name="fk_datasets_upload_session_id",
            ondelete="SET NULL",
        ),
        sa.UniqueConstraint("physical_schema_name", "physical_table_name", name="uq_datasets_physical_table"),
    )
    op.create_index("idx_datasets_user_status", "datasets", ["user_id", "status"])
    op.create_index("idx_datasets_user_created", "datasets", ["user_id", sa.text("created_at DESC")])

    op.create_table(
        "dataset_columns",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("dataset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("column_index", sa.Integer(), nullable=False),
        sa.Column("column_name", sa.Text(), nullable=False),
        sa.Column("original_column_name", sa.Text(), nullable=False),
        sa.Column("postgres_type", sa.Text(), nullable=False),
        sa.Column("pandas_type", sa.Text(), nullable=True),
        sa.Column("semantic_type", sa.Text(), nullable=False),
        sa.Column("nullable_count", sa.BigInteger(), nullable=False, server_default=sa.text("0")),
        sa.Column("nullable_ratio", sa.Double(), nullable=False, server_default=sa.text("0")),
        sa.Column("distinct_count", sa.BigInteger(), nullable=True),
        sa.Column("sample_values", postgresql.JSONB(), nullable=True),
        sa.Column("min_value", sa.Text(), nullable=True),
        sa.Column("max_value", sa.Text(), nullable=True),
        sa.Column("warning_flags", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "semantic_type IN ('identifier', 'datetime', 'numeric', 'currency', 'category', 'boolean', 'text', 'unknown')",
            name="ck_dataset_columns_semantic_type",
        ),
        sa.ForeignKeyConstraint(
            ["dataset_id"],
            ["datasets.id"],
            name="fk_dataset_columns_dataset_id",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("dataset_id", "column_name", name="uq_dataset_columns_dataset_column_name"),
        sa.UniqueConstraint("dataset_id", "column_index", name="uq_dataset_columns_dataset_column_index"),
    )
    op.create_index("idx_dataset_columns_dataset", "dataset_columns", ["dataset_id"])
    op.create_index("idx_dataset_columns_dataset_semantic", "dataset_columns", ["dataset_id", "semantic_type"])

    op.create_table(
        "dataset_quality_issues",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("dataset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("column_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("issue_type", sa.Text(), nullable=False),
        sa.Column("severity", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("affected_row_count", sa.BigInteger(), nullable=True),
        sa.Column("affected_ratio", sa.Double(), nullable=True),
        sa.Column("sample_values", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "issue_type IN ('missing_values', 'exact_duplicates_removed', 'high_missing_ratio', 'mostly_empty_column', 'constant_column', 'high_cardinality_text', 'mixed_type_values', 'date_parse_failures', 'numeric_parse_failures', 'formula_like_values_detected', 'wide_cells_detected')",
            name="ck_dataset_quality_issues_issue_type",
        ),
        sa.CheckConstraint("severity IN ('info', 'warning', 'critical')", name="ck_dataset_quality_issues_severity"),
        sa.ForeignKeyConstraint(
            ["dataset_id"],
            ["datasets.id"],
            name="fk_dataset_quality_issues_dataset_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["column_id"],
            ["dataset_columns.id"],
            name="fk_dataset_quality_issues_column_id",
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        "idx_quality_issues_dataset_severity",
        "dataset_quality_issues",
        ["dataset_id", "severity"],
    )

    op.create_table(
        "chat_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("dataset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.Text(), nullable=False, server_default=sa.text("'New investigation'")),
        sa.Column("memory_summary", sa.Text(), nullable=True),
        sa.Column("memory_summary_version", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("last_summarized_message_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("memory_token_estimate", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["app_users.id"], name="fk_chat_sessions_user_id", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"], name="fk_chat_sessions_dataset_id", ondelete="CASCADE"),
    )
    op.create_index("idx_chat_sessions_user_updated", "chat_sessions", ["user_id", sa.text("updated_at DESC")])
    op.create_index("idx_chat_sessions_dataset", "chat_sessions", ["dataset_id"])
    op.create_index(
        "idx_chat_sessions_one_active_per_dataset",
        "chat_sessions",
        ["dataset_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "chat_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("chat_session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("message_index", sa.BigInteger(), nullable=False),
        sa.Column("client_message_id", sa.Text(), nullable=True),
        sa.Column("idempotency_body_hash", sa.Text(), nullable=True),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("blocks", postgresql.JSONB(), nullable=True),
        sa.Column("token_estimate", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("role IN ('user', 'assistant', 'system')", name="ck_chat_messages_role"),
        sa.CheckConstraint(
            "role <> 'user' OR client_message_id IS NOT NULL",
            name="ck_chat_messages_user_client_message_id",
        ),
        sa.ForeignKeyConstraint(
            ["chat_session_id"],
            ["chat_sessions.id"],
            name="fk_chat_messages_chat_session_id",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("chat_session_id", "message_index", name="uq_chat_messages_chat_message_index"),
        sa.UniqueConstraint(
            "chat_session_id",
            "client_message_id",
            name="uq_chat_messages_chat_client_message_id",
        ),
    )
    op.create_index("idx_chat_messages_chat_index", "chat_messages", ["chat_session_id", "message_index"])
    op.create_index("idx_chat_messages_chat_created", "chat_messages", ["chat_session_id", "created_at"])
    op.create_foreign_key(
        "fk_chat_sessions_last_summarized_message_id",
        "chat_sessions",
        "chat_messages",
        ["last_summarized_message_id"],
        ["id"],
        deferrable=True,
        initially="DEFERRED",
    )

    op.create_table(
        "analysis_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("chat_session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_message_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assistant_message_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("current_stage", sa.Text(), nullable=True),
        sa.Column("intent", sa.Text(), nullable=True),
        sa.Column("planner_output", postgresql.JSONB(), nullable=True),
        sa.Column("memory_context", postgresql.JSONB(), nullable=True),
        sa.Column("graph_trace", postgresql.JSONB(), nullable=True),
        sa.Column("checkpoint_thread_id", sa.Text(), nullable=True),
        sa.Column("checkpoint_run_id", sa.Text(), nullable=True),
        sa.Column("error_code", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_duration_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "status IN ('queued', 'running', 'success', 'partial_success', 'failed', 'cancelled')",
            name="ck_analysis_runs_status",
        ),
        sa.CheckConstraint(
            "current_stage IS NULL OR current_stage IN ('queued', 'loading_context', 'planning', 'querying', 'synthesizing', 'building_response', 'completed', 'failed')",
            name="ck_analysis_runs_current_stage",
        ),
        sa.CheckConstraint(
            "intent IS NULL OR intent IN ('data_question', 'schema_question', 'quality_question', 'summary_question', 'unsupported_question')",
            name="ck_analysis_runs_intent",
        ),
        sa.ForeignKeyConstraint(
            ["chat_session_id"],
            ["chat_sessions.id"],
            name="fk_analysis_runs_chat_session_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_message_id"],
            ["chat_messages.id"],
            name="fk_analysis_runs_user_message_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["assistant_message_id"],
            ["chat_messages.id"],
            name="fk_analysis_runs_assistant_message_id",
            ondelete="SET NULL",
        ),
        sa.UniqueConstraint("user_message_id", name="uq_analysis_runs_user_message_id"),
    )
    op.create_index("idx_analysis_runs_chat_started", "analysis_runs", ["chat_session_id", sa.text("started_at DESC")])
    op.create_index("idx_analysis_runs_status_created", "analysis_runs", ["status", "created_at"])

    op.create_table(
        "query_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("analysis_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("step_index", sa.Integer(), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("purpose", sa.Text(), nullable=True),
        sa.Column("generated_sql", sa.Text(), nullable=True),
        sa.Column("validated_sql", sa.Text(), nullable=True),
        sa.Column("validation_status", sa.Text(), nullable=True),
        sa.Column("execution_status", sa.Text(), nullable=True),
        sa.Column("repair_reason", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("execution_time_ms", sa.Integer(), nullable=True),
        sa.Column("row_count", sa.Integer(), nullable=True),
        sa.Column("result_columns", postgresql.JSONB(), nullable=True),
        sa.Column("result_preview", postgresql.JSONB(), nullable=True),
        sa.Column("result_summary", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "validation_status IS NULL OR validation_status IN ('pending', 'valid', 'invalid')",
            name="ck_query_attempts_validation_status",
        ),
        sa.CheckConstraint(
            "execution_status IS NULL OR execution_status IN ('not_run', 'success', 'failed', 'timeout')",
            name="ck_query_attempts_execution_status",
        ),
        sa.ForeignKeyConstraint(
            ["analysis_run_id"],
            ["analysis_runs.id"],
            name="fk_query_attempts_analysis_run_id",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("analysis_run_id", "step_index", "attempt_number", name="uq_query_attempts_run_step_attempt"),
    )
    op.create_index("idx_query_attempts_run_step", "query_attempts", ["analysis_run_id", "step_index", "attempt_number"])


def downgrade() -> None:
    op.drop_index("idx_query_attempts_run_step", table_name="query_attempts")
    op.drop_table("query_attempts")
    op.drop_index("idx_analysis_runs_status_created", table_name="analysis_runs")
    op.drop_index("idx_analysis_runs_chat_started", table_name="analysis_runs")
    op.drop_table("analysis_runs")
    op.drop_constraint("fk_chat_sessions_last_summarized_message_id", "chat_sessions", type_="foreignkey")
    op.drop_index("idx_chat_messages_chat_created", table_name="chat_messages")
    op.drop_index("idx_chat_messages_chat_index", table_name="chat_messages")
    op.drop_table("chat_messages")
    op.drop_index("idx_chat_sessions_one_active_per_dataset", table_name="chat_sessions")
    op.drop_index("idx_chat_sessions_dataset", table_name="chat_sessions")
    op.drop_index("idx_chat_sessions_user_updated", table_name="chat_sessions")
    op.drop_table("chat_sessions")
    op.drop_index("idx_quality_issues_dataset_severity", table_name="dataset_quality_issues")
    op.drop_table("dataset_quality_issues")
    op.drop_index("idx_dataset_columns_dataset_semantic", table_name="dataset_columns")
    op.drop_index("idx_dataset_columns_dataset", table_name="dataset_columns")
    op.drop_table("dataset_columns")
    op.drop_index("idx_datasets_user_created", table_name="datasets")
    op.drop_index("idx_datasets_user_status", table_name="datasets")
    op.drop_table("datasets")
    op.drop_index("idx_upload_sessions_expires_at", table_name="upload_sessions")
    op.drop_index("idx_upload_sessions_user_status", table_name="upload_sessions")
    op.drop_table("upload_sessions")
    op.drop_index("idx_app_users_clerk_user_id", table_name="app_users")
    op.drop_table("app_users")
    op.execute("DROP SCHEMA IF EXISTS user_data CASCADE")
    op.execute("DROP EXTENSION IF EXISTS vector")
    op.execute("DROP EXTENSION IF EXISTS pgcrypto")

