import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Double,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class SoftDeleteMixin:
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AppUser(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "app_users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clerk_user_id: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    email: Mapped[str | None] = mapped_column(Text, nullable=True)
    first_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (Index("idx_app_users_clerk_user_id", "clerk_user_id", unique=True),)


class UploadSession(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "upload_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("app_users.id", ondelete="CASCADE"),
        nullable=False,
    )
    original_filename: Mapped[str] = mapped_column(Text, nullable=False)
    file_extension: Mapped[str] = mapped_column(Text, nullable=False)
    temp_file_key: Mapped[str] = mapped_column(Text, nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    sheet_names: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    selected_sheet_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    preview_rows: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB, nullable=True)
    detected_columns: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB, nullable=True)
    warnings: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'[]'::jsonb"),
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        CheckConstraint("file_extension IN ('csv', 'xlsx')", name="ck_upload_sessions_file_extension"),
        CheckConstraint(
            "status IN ('uploaded', 'inspected', 'ingested', 'expired', 'failed', 'deleted')",
            name="ck_upload_sessions_status",
        ),
        Index("idx_upload_sessions_user_status", "user_id", "status"),
        Index("idx_upload_sessions_expires_at", "expires_at"),
    )


class Dataset(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "datasets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("app_users.id", ondelete="CASCADE"),
        nullable=False,
    )
    upload_session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("upload_sessions.id", ondelete="SET NULL"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    original_filename: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_file_type: Mapped[str] = mapped_column(Text, nullable=False)
    selected_sheet_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    physical_schema_name: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=text("'user_data'"),
    )
    physical_table_name: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    original_row_count: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))
    row_count: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))
    duplicate_rows_removed: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        server_default=text("0"),
    )
    column_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    total_missing_values: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        server_default=text("0"),
    )
    quality_status: Mapped[str | None] = mapped_column(Text, nullable=True)
    quality_score: Mapped[float | None] = mapped_column(Double, nullable=True)
    ingestion_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_file_deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    physical_table_dropped_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("physical_schema_name", "physical_table_name", name="uq_datasets_physical_table"),
        CheckConstraint("source_file_type IN ('csv', 'xlsx')", name="ck_datasets_source_file_type"),
        CheckConstraint(
            "status IN ('processing', 'ready', 'locked', 'failed', 'deleted')",
            name="ck_datasets_status",
        ),
        CheckConstraint(
            "quality_status IS NULL OR quality_status IN ('good', 'warning', 'poor')",
            name="ck_datasets_quality_status",
        ),
        Index("idx_datasets_user_status", "user_id", "status"),
        Index("idx_datasets_user_created", "user_id", "created_at"),
    )


class DatasetColumn(Base):
    __tablename__ = "dataset_columns"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
    )
    column_index: Mapped[int] = mapped_column(Integer, nullable=False)
    column_name: Mapped[str] = mapped_column(Text, nullable=False)
    original_column_name: Mapped[str] = mapped_column(Text, nullable=False)
    postgres_type: Mapped[str] = mapped_column(Text, nullable=False)
    pandas_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    semantic_type: Mapped[str] = mapped_column(Text, nullable=False)
    nullable_count: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))
    nullable_ratio: Mapped[float] = mapped_column(Double, nullable=False, server_default=text("0"))
    distinct_count: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    sample_values: Mapped[list[Any] | None] = mapped_column(JSONB, nullable=True)
    min_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    max_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    warning_flags: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'[]'::jsonb"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        UniqueConstraint("dataset_id", "column_name", name="uq_dataset_columns_dataset_column_name"),
        UniqueConstraint("dataset_id", "column_index", name="uq_dataset_columns_dataset_column_index"),
        CheckConstraint(
            "semantic_type IN ('identifier', 'datetime', 'numeric', 'currency', 'category', 'boolean', 'text', 'unknown')",
            name="ck_dataset_columns_semantic_type",
        ),
        Index("idx_dataset_columns_dataset", "dataset_id"),
        Index("idx_dataset_columns_dataset_semantic", "dataset_id", "semantic_type"),
    )


class DatasetQualityIssue(Base):
    __tablename__ = "dataset_quality_issues"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
    )
    column_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dataset_columns.id", ondelete="CASCADE"),
        nullable=True,
    )
    issue_type: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    affected_row_count: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    affected_ratio: Mapped[float | None] = mapped_column(Double, nullable=True)
    sample_values: Mapped[list[Any] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        CheckConstraint(
            "issue_type IN ('missing_values', 'exact_duplicates_removed', 'high_missing_ratio', 'mostly_empty_column', 'constant_column', 'high_cardinality_text', 'mixed_type_values', 'date_parse_failures', 'numeric_parse_failures', 'formula_like_values_detected', 'wide_cells_detected')",
            name="ck_dataset_quality_issues_issue_type",
        ),
        CheckConstraint(
            "severity IN ('info', 'warning', 'critical')",
            name="ck_dataset_quality_issues_severity",
        ),
        Index("idx_quality_issues_dataset_severity", "dataset_id", "severity"),
    )


class ChatSession(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "chat_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("app_users.id", ondelete="CASCADE"),
        nullable=False,
    )
    dataset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'New investigation'"))
    memory_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    memory_summary_version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    last_summarized_message_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "chat_messages.id",
            deferrable=True,
            initially="DEFERRED",
            use_alter=True,
            name="fk_chat_sessions_last_summarized_message_id",
        ),
        nullable=True,
    )
    memory_token_estimate: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))

    __table_args__ = (
        Index("idx_chat_sessions_user_updated", "user_id", "updated_at"),
        Index("idx_chat_sessions_dataset", "dataset_id"),
        Index(
            "idx_chat_sessions_one_active_per_dataset",
            "dataset_id",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )


class ChatMessage(Base, SoftDeleteMixin):
    __tablename__ = "chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    message_index: Mapped[int] = mapped_column(BigInteger, nullable=False)
    client_message_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    idempotency_body_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    role: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    blocks: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB, nullable=True)
    token_estimate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        UniqueConstraint("chat_session_id", "message_index", name="uq_chat_messages_chat_message_index"),
        UniqueConstraint("chat_session_id", "client_message_id", name="uq_chat_messages_chat_client_message_id"),
        CheckConstraint("role IN ('user', 'assistant', 'system')", name="ck_chat_messages_role"),
        CheckConstraint(
            "role <> 'user' OR client_message_id IS NOT NULL",
            name="ck_chat_messages_user_client_message_id",
        ),
        Index("idx_chat_messages_chat_index", "chat_session_id", "message_index"),
        Index("idx_chat_messages_chat_created", "chat_session_id", "created_at"),
    )


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chat_messages.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    assistant_message_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chat_messages.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(Text, nullable=False)
    current_stage: Mapped[str | None] = mapped_column(Text, nullable=True)
    intent: Mapped[str | None] = mapped_column(Text, nullable=True)
    planner_output: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    memory_context: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    graph_trace: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    checkpoint_thread_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    checkpoint_run_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        UniqueConstraint("user_message_id", name="uq_analysis_runs_user_message_id"),
        CheckConstraint(
            "status IN ('queued', 'running', 'success', 'partial_success', 'failed', 'cancelled')",
            name="ck_analysis_runs_status",
        ),
        CheckConstraint(
            "current_stage IS NULL OR current_stage IN ('queued', 'loading_context', 'planning', 'querying', 'synthesizing', 'building_response', 'completed', 'failed')",
            name="ck_analysis_runs_current_stage",
        ),
        CheckConstraint(
            "intent IS NULL OR intent IN ('data_question', 'schema_question', 'quality_question', 'summary_question', 'unsupported_question')",
            name="ck_analysis_runs_intent",
        ),
        Index("idx_analysis_runs_chat_started", "chat_session_id", "started_at"),
        Index("idx_analysis_runs_status_created", "status", "created_at"),
    )


class QueryAttempt(Base):
    __tablename__ = "query_attempts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analysis_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    step_index: Mapped[int] = mapped_column(Integer, nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    purpose: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_sql: Mapped[str | None] = mapped_column(Text, nullable=True)
    validated_sql: Mapped[str | None] = mapped_column(Text, nullable=True)
    validation_status: Mapped[str | None] = mapped_column(Text, nullable=True)
    execution_status: Mapped[str | None] = mapped_column(Text, nullable=True)
    repair_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    execution_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    result_columns: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    result_preview: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB, nullable=True)
    result_summary: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        UniqueConstraint(
            "analysis_run_id",
            "step_index",
            "attempt_number",
            name="uq_query_attempts_run_step_attempt",
        ),
        CheckConstraint(
            "validation_status IS NULL OR validation_status IN ('pending', 'valid', 'invalid')",
            name="ck_query_attempts_validation_status",
        ),
        CheckConstraint(
            "execution_status IS NULL OR execution_status IN ('not_run', 'success', 'failed', 'timeout')",
            name="ck_query_attempts_execution_status",
        ),
        Index("idx_query_attempts_run_step", "analysis_run_id", "step_index", "attempt_number"),
    )
