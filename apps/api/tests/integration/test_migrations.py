import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError

from app.core.config import get_settings


EXPECTED_TABLES = {
    "app_users",
    "upload_sessions",
    "datasets",
    "dataset_columns",
    "dataset_quality_issues",
    "chat_sessions",
    "chat_messages",
    "analysis_runs",
    "query_attempts",
}

EXPECTED_INDEXES = {
    "app_users": {"idx_app_users_clerk_user_id"},
    "upload_sessions": {"idx_upload_sessions_user_status", "idx_upload_sessions_expires_at"},
    "datasets": {"idx_datasets_user_status", "idx_datasets_user_created"},
    "dataset_columns": {"idx_dataset_columns_dataset", "idx_dataset_columns_dataset_semantic"},
    "dataset_quality_issues": {"idx_quality_issues_dataset_severity"},
    "chat_sessions": {
        "idx_chat_sessions_user_updated",
        "idx_chat_sessions_dataset",
        "idx_chat_sessions_one_active_per_dataset",
    },
    "chat_messages": {"idx_chat_messages_chat_index", "idx_chat_messages_chat_created"},
    "analysis_runs": {"idx_analysis_runs_chat_started", "idx_analysis_runs_status_created"},
    "query_attempts": {"idx_query_attempts_run_step"},
}

EXPECTED_CHECKS = {
    "upload_sessions": {"ck_upload_sessions_file_extension", "ck_upload_sessions_status"},
    "datasets": {"ck_datasets_source_file_type", "ck_datasets_status", "ck_datasets_quality_status"},
    "dataset_columns": {"ck_dataset_columns_semantic_type"},
    "dataset_quality_issues": {
        "ck_dataset_quality_issues_issue_type",
        "ck_dataset_quality_issues_severity",
    },
    "chat_messages": {"ck_chat_messages_role", "ck_chat_messages_user_client_message_id"},
    "analysis_runs": {
        "ck_analysis_runs_status",
        "ck_analysis_runs_current_stage",
        "ck_analysis_runs_intent",
    },
    "query_attempts": {
        "ck_query_attempts_validation_status",
        "ck_query_attempts_execution_status",
    },
}


@pytest.fixture(scope="module")
def db_engine():
    engine = create_engine(get_settings().database_url)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def base_records(db_engine):
    unique = uuid.uuid4().hex
    user_id = uuid.uuid4()
    upload_session_id = uuid.uuid4()
    dataset_id = uuid.uuid4()
    chat_id = uuid.uuid4()
    user_message_id = uuid.uuid4()
    expires_at = datetime.now(UTC) + timedelta(minutes=30)

    with db_engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO app_users (id, clerk_user_id, email)
                VALUES (:id, :clerk_user_id, :email)
                """
            ),
            {"id": user_id, "clerk_user_id": f"user_{unique}", "email": f"{unique}@example.com"},
        )
        conn.execute(
            text(
                """
                INSERT INTO upload_sessions (
                    id, user_id, original_filename, file_extension, temp_file_key,
                    file_size_bytes, status, expires_at
                )
                VALUES (
                    :id, :user_id, 'sales.csv', 'csv', :temp_file_key,
                    128, 'inspected', :expires_at
                )
                """
            ),
            {
                "id": upload_session_id,
                "user_id": user_id,
                "temp_file_key": f"uploads/{unique}.csv",
                "expires_at": expires_at,
            },
        )
        conn.execute(
            text(
                """
                INSERT INTO datasets (
                    id, user_id, upload_session_id, name, original_filename,
                    source_file_type, physical_table_name, status
                )
                VALUES (
                    :id, :user_id, :upload_session_id, 'Sales', 'sales.csv',
                    'csv', :physical_table_name, 'ready'
                )
                """
            ),
            {
                "id": dataset_id,
                "user_id": user_id,
                "upload_session_id": upload_session_id,
                "physical_table_name": f"dataset_{unique}",
            },
        )
        conn.execute(
            text(
                """
                INSERT INTO chat_sessions (id, user_id, dataset_id, title)
                VALUES (:id, :user_id, :dataset_id, 'New investigation')
                """
            ),
            {"id": chat_id, "user_id": user_id, "dataset_id": dataset_id},
        )
        conn.execute(
            text(
                """
                INSERT INTO chat_messages (
                    id, chat_session_id, message_index, client_message_id, role, content
                )
                VALUES (:id, :chat_session_id, 1, :client_message_id, 'user', 'Show revenue')
                """
            ),
            {
                "id": user_message_id,
                "chat_session_id": chat_id,
                "client_message_id": f"msg_{unique}",
            },
        )

    return {
        "user_id": user_id,
        "upload_session_id": upload_session_id,
        "dataset_id": dataset_id,
        "chat_id": chat_id,
        "user_message_id": user_message_id,
        "unique": unique,
    }


def test_expected_tables_exist(db_engine):
    inspector = inspect(db_engine)

    assert EXPECTED_TABLES.issubset(set(inspector.get_table_names()))
    assert "user_data" in inspector.get_schema_names()


def test_expected_indexes_exist(db_engine):
    inspector = inspect(db_engine)

    for table_name, expected_indexes in EXPECTED_INDEXES.items():
        actual_indexes = {index["name"] for index in inspector.get_indexes(table_name)}
        assert expected_indexes.issubset(actual_indexes)


def test_expected_check_constraints_exist(db_engine):
    inspector = inspect(db_engine)

    for table_name, expected_checks in EXPECTED_CHECKS.items():
        actual_checks = {constraint["name"] for constraint in inspector.get_check_constraints(table_name)}
        assert expected_checks.issubset(actual_checks)


def test_user_message_without_client_message_id_fails(db_engine, base_records):
    with pytest.raises(IntegrityError), db_engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO chat_messages (chat_session_id, message_index, role, content)
                VALUES (:chat_session_id, 2, 'user', 'Missing idempotency key')
                """
            ),
            {"chat_session_id": base_records["chat_id"]},
        )


def test_duplicate_message_index_in_same_chat_fails(db_engine, base_records):
    with pytest.raises(IntegrityError), db_engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO chat_messages (
                    chat_session_id, message_index, client_message_id, role, content
                )
                VALUES (:chat_session_id, 1, :client_message_id, 'user', 'Duplicate index')
                """
            ),
            {"chat_session_id": base_records["chat_id"], "client_message_id": f"dup_{uuid.uuid4().hex}"},
        )


def test_duplicate_client_message_id_in_same_chat_fails(db_engine, base_records):
    with pytest.raises(IntegrityError), db_engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO chat_messages (
                    chat_session_id, message_index, client_message_id, role, content
                )
                VALUES (:chat_session_id, 2, :client_message_id, 'user', 'Duplicate key')
                """
            ),
            {
                "chat_session_id": base_records["chat_id"],
                "client_message_id": f"msg_{base_records['unique']}",
            },
        )


def test_duplicate_analysis_run_for_same_user_message_id_fails(db_engine, base_records):
    with db_engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO analysis_runs (chat_session_id, user_message_id, status, current_stage)
                VALUES (:chat_session_id, :user_message_id, 'queued', 'queued')
                """
            ),
            {
                "chat_session_id": base_records["chat_id"],
                "user_message_id": base_records["user_message_id"],
            },
        )

    with pytest.raises(IntegrityError), db_engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO analysis_runs (chat_session_id, user_message_id, status, current_stage)
                VALUES (:chat_session_id, :user_message_id, 'queued', 'queued')
                """
            ),
            {
                "chat_session_id": base_records["chat_id"],
                "user_message_id": base_records["user_message_id"],
            },
        )

