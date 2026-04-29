from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.api.deps import get_current_user
from app.core.database import SessionLocal
from app.db.models import AnalysisRun, AppUser, ChatMessage, ChatSession, Dataset, DatasetColumn, DatasetQualityIssue, QueryAttempt, UploadSession
from app.main import app
from app.workers.analysis_worker import AnalysisWorker
from app.workers.dataset_worker import DatasetWorker


@pytest.fixture
def workflow_user() -> AppUser:
    async def create_user() -> AppUser:
        user = AppUser(clerk_user_id=f"user_workflow_{uuid.uuid4().hex}", email="workflow@example.com")
        async with SessionLocal() as session:
            session.add(user)
            await session.commit()
            await session.refresh(user)
        return user

    import asyncio

    user = asyncio.run(create_user())
    yield user

    async def cleanup() -> None:
        async with SessionLocal() as session:
            await session.execute(delete(QueryAttempt))
            await session.execute(delete(AnalysisRun))
            await session.execute(delete(ChatMessage))
            await session.execute(delete(ChatSession))
            await session.execute(delete(DatasetQualityIssue))
            await session.execute(delete(DatasetColumn))
            await session.execute(delete(Dataset).where(Dataset.user_id == user.id))
            await session.execute(delete(UploadSession).where(UploadSession.user_id == user.id))
            await session.execute(delete(AppUser).where(AppUser.id == user.id))
            await session.commit()

    asyncio.run(cleanup())


@pytest.fixture
def workflow_client(workflow_user: AppUser) -> TestClient:
    async def override_current_user() -> AppUser:
        return workflow_user

    app.dependency_overrides[get_current_user] = override_current_user
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_dataset_to_chat_to_analysis_blocks_workflow(workflow_client: TestClient) -> None:
    upload = workflow_client.post(
        "/api/v1/upload-sessions",
        files={"file": ("sales.csv", "region,revenue\nWest,100\nWest,100\nEast,\n", "text/csv")},
    )
    assert upload.status_code == 201
    upload_id = upload.json()["data"]["id"]

    dataset_response = workflow_client.post("/api/v1/datasets", json={"upload_session_id": upload_id, "name": "Sales"})
    assert dataset_response.status_code == 202
    dataset_id = dataset_response.json()["data"]["id"]

    import asyncio

    assert asyncio.run(DatasetWorker().run_once()) >= 1
    dataset = workflow_client.get(f"/api/v1/datasets/{dataset_id}").json()["data"]
    assert dataset["status"] == "ready"
    assert dataset["row_count"] == 2

    preview = workflow_client.get(f"/api/v1/datasets/{dataset_id}/preview")
    assert preview.status_code == 200
    assert preview.json()["data"][0]["_sherlock_row_hash"]

    columns = workflow_client.get(f"/api/v1/datasets/{dataset_id}/columns").json()["data"]
    issues = workflow_client.get(f"/api/v1/datasets/{dataset_id}/quality-issues").json()["data"]
    assert columns
    assert issues

    chat = workflow_client.post("/api/v1/chats", json={"dataset_id": dataset_id})
    assert chat.status_code == 201
    chat_id = chat.json()["data"]["id"]

    message = workflow_client.post(
        f"/api/v1/chats/{chat_id}/messages",
        json={"content": "How many rows are there?"},
        headers={"Idempotency-Key": "workflow-row-count"},
    )
    assert message.status_code == 202
    run_id = message.json()["data"]["analysis_run_id"]

    assert asyncio.run(AnalysisWorker().run_once()) >= 1
    run = workflow_client.get(f"/api/v1/analysis-runs/{run_id}").json()["data"]
    assert run["status"] == "success"
    assert run["assistant_message"]["blocks"]
