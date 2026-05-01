from app.services.sql_validation_service import SqlValidationService


def validator() -> SqlValidationService:
    return SqlValidationService()


def test_valid_select_on_current_table_passes() -> None:
    result = validator().validate('SELECT revenue FROM user_data."dataset_abc"', table_name="dataset_abc", allowed_columns={"revenue"})

    assert result.is_valid
    assert result.sql and "LIMIT 1000" in result.sql


def test_with_select_on_current_table_passes() -> None:
    result = validator().validate(
        'WITH rows AS (SELECT revenue FROM user_data."dataset_abc") SELECT revenue FROM rows',
        table_name="dataset_abc",
        allowed_columns={"revenue"},
    )

    assert result.is_valid


def test_select_from_other_user_data_table_rejected() -> None:
    result = validator().validate('SELECT revenue FROM user_data."dataset_other"', table_name="dataset_abc", allowed_columns={"revenue"})

    assert not result.is_valid


def test_blocked_schemas_rejected() -> None:
    for schema in ("public", "information_schema", "pg_catalog"):
        result = validator().validate(f"SELECT id FROM {schema}.users", table_name="dataset_abc", allowed_columns={"id"})
        assert not result.is_valid


def test_writes_multiple_statements_comments_and_unknown_columns_rejected() -> None:
    checks = [
        "INSERT INTO user_data.dataset_abc VALUES (1)",
        "DROP TABLE user_data.dataset_abc",
        'SELECT revenue FROM user_data."dataset_abc"; SELECT 1',
        'SELECT revenue FROM user_data."dataset_abc" -- hidden',
        'SELECT unknown FROM user_data."dataset_abc"',
        'SELECT pg_sleep(1) FROM user_data."dataset_abc"',
    ]

    for sql in checks:
        result = validator().validate(sql, table_name="dataset_abc", allowed_columns={"revenue"})
        assert not result.is_valid
