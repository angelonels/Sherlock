import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.db.models import AppUser
from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def test_user() -> AppUser:
    return AppUser(
        clerk_user_id="user_test",
        email="user@example.com",
        first_name="Aman",
        last_name="Sharma",
        image_url="https://example.com/avatar.png",
    )


@pytest.fixture
def authenticated_client(test_user: AppUser) -> TestClient:
    async def override_current_user() -> AppUser:
        return test_user

    app.dependency_overrides[get_current_user] = override_current_user
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_current_user, None)

