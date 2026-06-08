from app.core.config import Settings
from app.core.production_config import production_config_issues


def production_settings(**overrides) -> Settings:
    values = {
        "_env_file": None,
        "app_env": "production",
        "frontend_origin": "https://sherlock.example.org",
        "cors_origins": ["https://sherlock.example.org"],
        "clerk_jwks_url": "https://clerk.example.org/.well-known/jwks.json",
        "clerk_secret_key": "configured-clerk-secret",
        "clerk_authorized_parties": ["https://sherlock.example.org"],
        "database_url": "postgresql+psycopg://sherlock_admin:strong-admin@postgres:5432/sherlock",
        "readonly_database_url": "postgresql+psycopg://sherlock_readonly:strong-readonly@postgres:5432/sherlock",
        "redis_url": "redis://redis:6379/0",
        "celery_broker_url": "redis://redis:6379/0",
        "celery_result_backend": "redis://redis:6379/1",
        "aws_access_key_id": "configured-access-key",
        "aws_secret_access_key": "configured-secret-key",
        "aws_default_region": "us-east-1",
        "bedrock_model_id": "meta.llama3-70b-instruct-v1:0",
    }
    values.update(overrides)
    return Settings(**values)


def test_valid_production_configuration_has_no_issues() -> None:
    issues = production_config_issues(
        production_settings(),
        {
            "POSTGRES_PASSWORD": "strong-admin-password",
            "POSTGRES_READONLY_PASSWORD": "strong-readonly-password",
            "POSTGRES_BACKUP_S3_URI": "s3://sherlock-backups/production",
            "POSTGRES_BACKUP_S3_ACCESS_KEY_ID": "backup-access-key",
            "POSTGRES_BACKUP_S3_SECRET_ACCESS_KEY": "backup-secret-key",
            "POSTGRES_BACKUP_S3_REGION": "us-east-1",
        },
    )

    assert issues == []


def test_placeholder_and_missing_production_values_are_rejected() -> None:
    issues = production_config_issues(
        production_settings(
            frontend_origin="https://your-vercel-app.vercel.app",
            cors_origins=["http://localhost:3000"],
            clerk_jwks_url=None,
            clerk_secret_key=None,
            clerk_authorized_parties=["https://different.example.org"],
            database_url="postgresql+psycopg://sherlock_admin:change_me@postgres:5432/sherlock",
            readonly_database_url="postgresql+psycopg://sherlock_admin:change_me@postgres:5432/sherlock",
            redis_url="",
            celery_broker_url="",
            celery_result_backend="",
            aws_access_key_id=None,
            aws_secret_access_key=None,
            aws_default_region=None,
            upload_max_file_size_bytes=26 * 1024 * 1024,
            upload_max_columns=101,
        ),
        {
            "POSTGRES_PASSWORD": "change_me",
            "POSTGRES_READONLY_PASSWORD": "",
            "POSTGRES_BACKUP_S3_URI": "s3://your-backup-bucket",
            "POSTGRES_BACKUP_S3_ACCESS_KEY_ID": "",
            "POSTGRES_BACKUP_S3_SECRET_ACCESS_KEY": "",
            "POSTGRES_BACKUP_S3_REGION": "",
        },
    )

    assert "FRONTEND_ORIGIN must be the public HTTPS frontend origin." in issues
    assert "CORS_ORIGINS must contain only public HTTPS origins." in issues
    assert "CLERK_AUTHORIZED_PARTIES must contain the production frontend origin." in issues
    assert "CLERK_JWKS_URL or CLERK_JWT_KEY is required." in issues
    assert "CLERK_SECRET_KEY is required." in issues
    assert "DATABASE_URL must use non-placeholder production credentials." in issues
    assert "READONLY_DATABASE_URL must use non-placeholder production credentials." in issues
    assert "CELERY_BROKER_URL or REDIS_URL must be configured." in issues
    assert "CELERY_RESULT_BACKEND or REDIS_URL must be configured." in issues
    assert "AWS_ACCESS_KEY_ID is required." in issues
    assert "AWS_SECRET_ACCESS_KEY is required." in issues
    assert "AWS_DEFAULT_REGION is required." in issues
    assert "UPLOAD_MAX_FILE_SIZE_BYTES must not exceed 25 MB." in issues
    assert "UPLOAD_MAX_COLUMNS must not exceed 100." in issues
    assert "POSTGRES_PASSWORD must be set to a non-placeholder value." in issues
    assert "POSTGRES_READONLY_PASSWORD must be set to a non-placeholder value." in issues
    assert "POSTGRES_BACKUP_S3_URI must be a non-placeholder s3:// destination." in issues
    assert "POSTGRES_BACKUP_S3_ACCESS_KEY_ID must be set for off-host backups." in issues
    assert "POSTGRES_BACKUP_S3_SECRET_ACCESS_KEY must be set for off-host backups." in issues
    assert "POSTGRES_BACKUP_S3_REGION must be set for off-host backups." in issues
