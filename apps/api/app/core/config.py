from functools import lru_cache
from typing import Annotated

from pydantic import AliasChoices, AnyUrl, BeforeValidator, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings.sources.types import NoDecode


def _split_origins(value: str | list[str]) -> list[str]:
    if isinstance(value, list):
        return value
    return [origin.strip() for origin in value.split(",") if origin.strip()]


CorsOrigins = Annotated[list[str], NoDecode, BeforeValidator(_split_origins)]


class Settings(BaseSettings):
    app_name: str = "Sherlock"
    app_env: str = "development"
    api_prefix: str = Field(
        default="/api/v1",
        validation_alias=AliasChoices("API_PREFIX", "API_V1_PREFIX"),
    )
    frontend_origin: str = "http://localhost:3000"
    cors_origins: CorsOrigins = Field(default_factory=lambda: ["http://localhost:3000"])
    database_url: str = "postgresql+psycopg://sherlock_admin:change_me@localhost:5432/sherlock_db"
    readonly_database_url: str | None = None
    request_id_header: str = "X-Request-ID"
    clerk_secret_key: str | None = None
    clerk_issuer_url: AnyUrl | None = None
    clerk_jwks_url: AnyUrl | None = None
    clerk_jwt_key: str | None = None
    clerk_audience: str | None = None
    clerk_authorized_parties: CorsOrigins = Field(default_factory=list)
    upload_tmp_dir: str = ".tmp/uploads"
    upload_session_ttl_minutes: int = 30
    upload_max_file_size_bytes: int = 25 * 1024 * 1024
    upload_max_columns: int = 100
    upload_max_cell_length: int = 20_000
    upload_preview_rows: int = 100
    xlsx_max_uncompressed_bytes: int = 100 * 1024 * 1024
    xlsx_max_compression_ratio: int = 100
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_default_region: str | None = None
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @property
    def effective_cors_origins(self) -> list[str]:
        origins = [self.frontend_origin, *self.cors_origins]
        return list(dict.fromkeys(origin for origin in origins if origin))

    @property
    def api_v1_prefix(self) -> str:
        return self.api_prefix

    @property
    def effective_readonly_database_url(self) -> str:
        return self.readonly_database_url or self.database_url

    @property
    def effective_clerk_issuer_url(self) -> str | None:
        if self.clerk_issuer_url:
            return str(self.clerk_issuer_url).rstrip("/")
        if not self.clerk_jwks_url:
            return None
        jwks_url = str(self.clerk_jwks_url).rstrip("/")
        suffix = "/.well-known/jwks.json"
        return jwks_url[: -len(suffix)] if jwks_url.endswith(suffix) else None

    @property
    def normalized_clerk_jwt_key(self) -> str | None:
        if not self.clerk_jwt_key:
            return None
        return self.clerk_jwt_key.replace("\\n", "\n")


@lru_cache
def get_settings() -> Settings:
    return Settings()
