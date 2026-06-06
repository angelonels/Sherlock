from __future__ import annotations

from collections.abc import Mapping

from app.core.config import Settings


PLACEHOLDER_MARKERS = ("change_me", "your-", "example.com", "<", ">")


def _is_placeholder(value: str | None) -> bool:
    normalized = (value or "").strip().lower()
    return not normalized or any(marker in normalized for marker in PLACEHOLDER_MARKERS)


def production_config_issues(settings: Settings, environment: Mapping[str, str]) -> list[str]:
    issues: list[str] = []
    if settings.app_env != "production":
        issues.append("APP_ENV must be production.")
    if _is_placeholder(settings.frontend_origin) or not settings.frontend_origin.startswith("https://"):
        issues.append("FRONTEND_ORIGIN must be the public HTTPS frontend origin.")
    if (
        not settings.cors_origins
        or any(_is_placeholder(origin) or not origin.startswith("https://") for origin in settings.cors_origins)
    ):
        issues.append("CORS_ORIGINS must contain only public HTTPS origins.")
    if (
        not settings.clerk_authorized_parties
        or settings.frontend_origin not in settings.clerk_authorized_parties
        or any(
            _is_placeholder(origin) or not origin.startswith("https://")
            for origin in settings.clerk_authorized_parties
        )
    ):
        issues.append("CLERK_AUTHORIZED_PARTIES must contain the production frontend origin.")
    if not settings.clerk_jwks_url and not settings.normalized_clerk_jwt_key:
        issues.append("CLERK_JWKS_URL or CLERK_JWT_KEY is required.")
    if _is_placeholder(settings.clerk_secret_key):
        issues.append("CLERK_SECRET_KEY is required.")
    if _is_placeholder(settings.database_url):
        issues.append("DATABASE_URL must use non-placeholder production credentials.")
    if _is_placeholder(settings.readonly_database_url):
        issues.append("READONLY_DATABASE_URL must use non-placeholder production credentials.")
    elif settings.readonly_database_url == settings.database_url:
        issues.append("READONLY_DATABASE_URL must use a separate readonly database role.")
    if _is_placeholder(settings.effective_celery_broker_url):
        issues.append("CELERY_BROKER_URL or REDIS_URL must be configured.")
    if _is_placeholder(settings.effective_celery_result_backend):
        issues.append("CELERY_RESULT_BACKEND or REDIS_URL must be configured.")
    if _is_placeholder(settings.aws_access_key_id):
        issues.append("AWS_ACCESS_KEY_ID is required.")
    if _is_placeholder(settings.aws_secret_access_key):
        issues.append("AWS_SECRET_ACCESS_KEY is required.")
    if _is_placeholder(settings.aws_default_region):
        issues.append("AWS_DEFAULT_REGION is required.")
    if _is_placeholder(settings.bedrock_model_id):
        issues.append("BEDROCK_MODEL_ID is required.")
    if settings.upload_max_file_size_bytes > 25 * 1024 * 1024:
        issues.append("UPLOAD_MAX_FILE_SIZE_BYTES must not exceed 25 MB.")
    if settings.upload_max_columns > 100:
        issues.append("UPLOAD_MAX_COLUMNS must not exceed 100.")

    for name in ("POSTGRES_PASSWORD", "POSTGRES_READONLY_PASSWORD"):
        if _is_placeholder(environment.get(name)):
            issues.append(f"{name} must be set to a non-placeholder value.")

    backup_s3_uri = environment.get("POSTGRES_BACKUP_S3_URI", "")
    if _is_placeholder(backup_s3_uri) or not backup_s3_uri.startswith("s3://"):
        issues.append("POSTGRES_BACKUP_S3_URI must be a non-placeholder s3:// destination.")
    for name in (
        "POSTGRES_BACKUP_S3_ACCESS_KEY_ID",
        "POSTGRES_BACKUP_S3_SECRET_ACCESS_KEY",
        "POSTGRES_BACKUP_S3_REGION",
    ):
        if _is_placeholder(environment.get(name)):
            issues.append(f"{name} must be set for off-host backups.")

    return issues
