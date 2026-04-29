from app.core.config import Settings


def test_settings_load_from_env(monkeypatch):
    monkeypatch.setenv("FRONTEND_ORIGIN", "https://app.example.com")
    monkeypatch.setenv("API_PREFIX", "/api/v1")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://user:pass@localhost:5432/sherlock")
    monkeypatch.setenv("CLERK_JWKS_URL", "https://clerk.example.com/.well-known/jwks.json")
    monkeypatch.setenv("CLERK_AUTHORIZED_PARTIES", "https://app.example.com,http://localhost:3000")

    settings = Settings()

    assert settings.frontend_origin == "https://app.example.com"
    assert settings.api_prefix == "/api/v1"
    assert settings.api_v1_prefix == "/api/v1"
    assert settings.database_url == "postgresql+psycopg://user:pass@localhost:5432/sherlock"
    assert settings.effective_clerk_issuer_url == "https://clerk.example.com"
    assert settings.clerk_authorized_parties == ["https://app.example.com", "http://localhost:3000"]
    assert "https://app.example.com" in settings.effective_cors_origins


def test_settings_normalizes_multiline_clerk_jwt_key():
    settings = Settings(clerk_jwt_key="-----BEGIN PUBLIC KEY-----\\nabc\\n-----END PUBLIC KEY-----")

    assert settings.normalized_clerk_jwt_key == "-----BEGIN PUBLIC KEY-----\nabc\n-----END PUBLIC KEY-----"
