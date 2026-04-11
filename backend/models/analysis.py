from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from database import Base
import uuid


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    __table_args__ = (
        UniqueConstraint("chat_session_id", "message_index"),
        UniqueConstraint("chat_session_id", "client_message_id"),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    chat_session_id = Column(String, ForeignKey("chat_sessions.id"), nullable=False, index=True)
    message_index = Column(BigInteger, nullable=False)
    client_message_id = Column(String, nullable=True)
    idempotency_body_hash = Column(String, nullable=True)
    role = Column(String, nullable=False)
    content = Column(String, nullable=True)
    blocks = Column(JSONB, nullable=True)
    token_estimate = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    chat_session_id = Column(String, ForeignKey("chat_sessions.id"), nullable=False, index=True)
    user_message_id = Column(String, ForeignKey("chat_messages.id"), nullable=False, unique=True)
    assistant_message_id = Column(String, ForeignKey("chat_messages.id"), nullable=True)
    status = Column(String, nullable=False, default="queued", index=True)
    current_stage = Column(String, nullable=True, default="queued")
    intent = Column(String, nullable=True)
    planner_output = Column(JSONB, nullable=True)
    memory_context = Column(JSONB, nullable=True)
    graph_trace = Column(JSONB, nullable=True)
    checkpoint_thread_id = Column(String, nullable=True)
    checkpoint_run_id = Column(String, nullable=True)
    error_code = Column(String, nullable=True)
    error_message = Column(String, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    total_duration_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class QueryAttempt(Base):
    __tablename__ = "query_attempts"
    __table_args__ = (UniqueConstraint("analysis_run_id", "step_index", "attempt_number"),)

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    analysis_run_id = Column(String, ForeignKey("analysis_runs.id"), nullable=False, index=True)
    step_index = Column(Integer, nullable=False)
    attempt_number = Column(Integer, nullable=False)
    purpose = Column(String, nullable=True)
    generated_sql = Column(String, nullable=True)
    validated_sql = Column(String, nullable=True)
    validation_status = Column(String, nullable=True)
    execution_status = Column(String, nullable=True)
    repair_reason = Column(String, nullable=True)
    error_message = Column(String, nullable=True)
    execution_time_ms = Column(Integer, nullable=True)
    row_count = Column(Integer, nullable=True)
    result_columns = Column(JSONB, nullable=True)
    result_preview = Column(JSONB, nullable=True)
    result_summary = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
