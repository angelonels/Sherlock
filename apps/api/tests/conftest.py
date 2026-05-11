import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.db.models import AppUser
from app.main import app
from app.services.job_dispatcher import JobDispatcher


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(autouse=True)
def disable_background_dispatch(monkeypatch, request):
    if request.node.get_closest_marker("enable_background_dispatch"):
        return
    monkeypatch.setattr(JobDispatcher, "enqueue_dataset_ingestion", lambda self, dataset_id: None)
    monkeypatch.setattr(JobDispatcher, "enqueue_analysis_run", lambda self, analysis_run_id: None)


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
