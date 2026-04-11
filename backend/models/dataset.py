from sqlalchemy import BigInteger, Column, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from database import Base
import uuid


class UploadSession(Base):
    __tablename__ = "upload_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String, ForeignKey("app_users.id"), nullable=False, index=True)
    original_filename = Column(String, nullable=False)
    file_extension = Column(String, nullable=False)
    temp_file_key = Column(String, nullable=False)
    file_size_bytes = Column(BigInteger, nullable=False)
    status = Column(String, nullable=False, default="uploaded", index=True)
    sheet_names = Column(JSONB, nullable=True)
    selected_sheet_name = Column(String, nullable=True)
    preview_rows = Column(JSONB, nullable=True)
    detected_columns = Column(JSONB, nullable=True)
    warnings = Column(JSONB, nullable=False, default=list)
    error_message = Column(String, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", backref="upload_sessions")


class Dataset(Base):
    __tablename__ = "datasets"
    __table_args__ = (UniqueConstraint("physical_schema_name", "physical_table_name"),)

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String, ForeignKey("app_users.id"), nullable=False, index=True)
    upload_session_id = Column(String, ForeignKey("upload_sessions.id"), nullable=True)
    name = Column(String, nullable=False)
    original_filename = Column(String, nullable=True)
    source_file_type = Column(String, nullable=False)
    selected_sheet_name = Column(String, nullable=True)
    physical_schema_name = Column(String, nullable=False, default="user_data")
    physical_table_name = Column(String, nullable=False)
    status = Column(String, nullable=False, default="processing", index=True)
    original_row_count = Column(BigInteger, nullable=False, default=0)
    row_count = Column(BigInteger, nullable=False, default=0)
    duplicate_rows_removed = Column(BigInteger, nullable=False, default=0)
    column_count = Column(Integer, nullable=False, default=0)
    total_missing_values = Column(BigInteger, nullable=False, default=0)
    quality_status = Column(String, nullable=True)
    quality_score = Column(Float, nullable=True)
    ingestion_error = Column(String, nullable=True)
    raw_file_deleted_at = Column(DateTime(timezone=True), nullable=True)
    physical_table_dropped_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    locked_at = Column(DateTime(timezone=True), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", backref="datasets")
    upload_session = relationship("UploadSession", backref="datasets")
    chat_sessions = relationship("ChatSession", back_populates="dataset")


class DatasetColumn(Base):
    __tablename__ = "dataset_columns"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    dataset_id = Column(String, ForeignKey("datasets.id"), nullable=False, index=True)
    column_index = Column(Integer, nullable=False)
    column_name = Column(String, nullable=False)
    original_column_name = Column(String, nullable=False)
    postgres_type = Column(String, nullable=False)
    pandas_type = Column(String, nullable=True)
    semantic_type = Column(String, nullable=False, default="unknown")
    nullable_count = Column(BigInteger, nullable=False, default=0)
    nullable_ratio = Column(Float, nullable=False, default=0)
    distinct_count = Column(BigInteger, nullable=True)
    sample_values = Column(JSONB, nullable=True)
    min_value = Column(String, nullable=True)
    max_value = Column(String, nullable=True)
    warning_flags = Column(JSONB, nullable=False, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class DatasetQualityIssue(Base):
    __tablename__ = "dataset_quality_issues"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    dataset_id = Column(String, ForeignKey("datasets.id"), nullable=False, index=True)
    column_id = Column(String, ForeignKey("dataset_columns.id"), nullable=True)
    issue_type = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    affected_row_count = Column(BigInteger, nullable=True)
    affected_ratio = Column(Float, nullable=True)
    sample_values = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
