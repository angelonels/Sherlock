import uuid

from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.core.config import Settings, get_settings
from app.db.models import AppUser
from app.main import app


def test_internal_endpoints_forbidden_in_production() -> None:
    async def override_user() -> AppUser:
        return AppUser(id=uuid.uuid4(), clerk_user_id="user_internal")

    def override_settings() -> Settings:
        return Settings(_env_file=None, app_env="production")

    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_settings] = override_settings
    try:
        response = TestClient(app).get(f"/api/v1/internal/analysis-runs/{uuid.uuid4()}/trace")
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_settings, None)

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"
