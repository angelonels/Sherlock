import asyncio
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.api.deps import get_current_user
from app.core.database import SessionLocal
from app.db.models import AnalysisRun, AppUser, ChatMessage, ChatSession, Dataset
from app.main import app
from app.services.job_dispatcher import JobDispatcher


@pytest.fixture
def persisted_chat_user() -> AppUser:
    async def create_user() -> AppUser:
        user = AppUser(clerk_user_id=f"user_chat_{uuid.uuid4().hex}", email="chat@example.com")
        async with SessionLocal() as session:
            session.add(user)
            await session.commit()
            await session.refresh(user)
        return user

    user = asyncio.run(create_user())
    yield user

    async def cleanup() -> None:
        async with SessionLocal() as session:
            await session.execute(delete(AnalysisRun))
            await session.execute(delete(ChatMessage))
            await session.execute(delete(ChatSession))
            await session.execute(delete(Dataset).where(Dataset.user_id == user.id))
            await session.execute(delete(AppUser).where(AppUser.id == user.id))
            await session.commit()

    asyncio.run(cleanup())


@pytest.fixture
def persisted_chat_client(persisted_chat_user: AppUser) -> TestClient:
    async def override_current_user() -> AppUser:
        return persisted_chat_user

    app.dependency_overrides[get_current_user] = override_current_user
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def create_ready_dataset(user: AppUser) -> Dataset:
    async def create_dataset() -> Dataset:
        dataset = Dataset(
            user_id=user.id,
            name="Sales",
            original_filename="sales.csv",
            source_file_type="csv",
            physical_table_name=f"dataset_{uuid.uuid4().hex}",
            status="ready",
            original_row_count=3,
            row_count=2,
            duplicate_rows_removed=1,
            column_count=2,
            total_missing_values=0,
            quality_status="good",
        )
        async with SessionLocal() as session:
            session.add(dataset)
            await session.commit()
            await session.refresh(dataset)
        return dataset

    return asyncio.run(create_dataset())


def test_list_chats_returns_empty_list_for_authenticated_user(authenticated_client):
    response = authenticated_client.get("/api/v1/chats")

    assert response.status_code == 200
    assert response.json() == {"data": [], "pagination": {"next_cursor": None}}


def test_create_chat_locks_dataset_and_rejects_second_active_chat(
    persisted_chat_client: TestClient,
    persisted_chat_user: AppUser,
) -> None:
    dataset = create_ready_dataset(persisted_chat_user)

    first_response = persisted_chat_client.post("/api/v1/chats", json={"dataset_id": str(dataset.id)})
    second_response = persisted_chat_client.post("/api/v1/chats", json={"dataset_id": str(dataset.id)})

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json()["error"]["code"] == "DATASET_NOT_READY"

    async def load_dataset_status() -> tuple[str, bool]:
        async with SessionLocal() as session:
            refreshed = await session.get(Dataset, dataset.id)
            assert refreshed is not None
            return refreshed.status, refreshed.locked_at is not None

    assert asyncio.run(load_dataset_status()) == ("locked", True)


def test_message_idempotency_returns_existing_run_and_rejects_body_conflict(
    persisted_chat_client: TestClient,
    persisted_chat_user: AppUser,
) -> None:
    dataset = create_ready_dataset(persisted_chat_user)
    chat_response = persisted_chat_client.post("/api/v1/chats", json={"dataset_id": str(dataset.id)})
    assert chat_response.status_code == 201
    chat_id = chat_response.json()["data"]["id"]

    first_response = persisted_chat_client.post(
        f"/api/v1/chats/{chat_id}/messages",
        json={"content": "How many rows are there?"},
        headers={"Idempotency-Key": "same-message"},
    )
    replay_response = persisted_chat_client.post(
        f"/api/v1/chats/{chat_id}/messages",
        json={"content": "How many rows are there?"},
        headers={"Idempotency-Key": "same-message"},
    )
    conflict_response = persisted_chat_client.post(
        f"/api/v1/chats/{chat_id}/messages",
        json={"content": "Show revenue by month"},
        headers={"Idempotency-Key": "same-message"},
    )

    assert first_response.status_code == 202
    assert replay_response.status_code == 202
    assert conflict_response.status_code == 409
    assert first_response.json()["data"]["message"]["id"] == replay_response.json()["data"]["message"]["id"]
    assert first_response.json()["data"]["analysis_run_id"] == replay_response.json()["data"]["analysis_run_id"]

    async def count_messages_and_runs() -> tuple[int, int]:
        async with SessionLocal() as session:
            messages = await session.execute(select(ChatMessage).where(ChatMessage.chat_session_id == uuid.UUID(chat_id)))
            runs = await session.execute(select(AnalysisRun).where(AnalysisRun.chat_session_id == uuid.UUID(chat_id)))
            return len(messages.scalars().all()), len(runs.scalars().all())

    assert asyncio.run(count_messages_and_runs()) == (1, 1)


@pytest.mark.enable_background_dispatch
def test_message_dispatch_failure_becomes_a_durable_recoverable_run(
    persisted_chat_client: TestClient,
    persisted_chat_user: AppUser,
    monkeypatch,
) -> None:
    dataset = create_ready_dataset(persisted_chat_user)
    chat_id = persisted_chat_client.post("/api/v1/chats", json={"dataset_id": str(dataset.id)}).json()["data"]["id"]

    def fail_dispatch(_self, _analysis_run_id) -> None:
        raise ConnectionError("broker unavailable with internal details")

    monkeypatch.setattr(JobDispatcher, "enqueue_analysis_run", fail_dispatch)
    response = persisted_chat_client.post(
        f"/api/v1/chats/{chat_id}/messages",
        json={"content": "How many rows are there?"},
        headers={"Idempotency-Key": "dispatch-failure"},
    )
    run_id = response.json()["data"]["analysis_run_id"]
    run = persisted_chat_client.get(f"/api/v1/analysis-runs/{run_id}").json()["data"]

    assert response.status_code == 202
    assert run["status"] == "failed"
    assert run["error_code"] == "ANALYSIS_DISPATCH_FAILED"
    assert run["error_message"] == "Sherlock could not start this analysis. Try asking the question again."
    assert "broker" not in run["error_message"]


def test_cross_tenant_resources_are_hidden_with_not_found(
    persisted_chat_client: TestClient,
) -> None:
    async def create_other_tenant_resources() -> tuple[uuid.UUID, uuid.UUID, uuid.UUID, uuid.UUID]:
        other_user_id = uuid.uuid4()
        dataset_id = uuid.uuid4()
        chat_id = uuid.uuid4()
        message_id = uuid.uuid4()
        run_id = uuid.uuid4()
        other_user = AppUser(
            id=other_user_id,
            clerk_user_id=f"user_other_tenant_{uuid.uuid4().hex}",
            email="other@example.com",
        )
        dataset = Dataset(
            id=dataset_id,
            user_id=other_user_id,
            name="Other tenant data",
            original_filename="other.csv",
            source_file_type="csv",
            physical_table_name=f"dataset_{uuid.uuid4().hex}",
            status="locked",
        )
        chat = ChatSession(
            id=chat_id,
            user_id=other_user_id,
            dataset_id=dataset_id,
            title="Other tenant chat",
        )
        message = ChatMessage(
            id=message_id,
            chat_session_id=chat_id,
            message_index=1,
            client_message_id="other-message",
            idempotency_body_hash="other",
            role="user",
            content="Private question",
        )
        run = AnalysisRun(
            id=run_id,
            chat_session_id=chat_id,
            user_message_id=message_id,
            status="queued",
            current_stage="queued",
        )
        async with SessionLocal() as session:
            session.add(other_user)
            await session.flush()
            session.add(dataset)
            await session.flush()
            session.add(chat)
            await session.flush()
            session.add(message)
            await session.flush()
            session.add(run)
            await session.commit()
        return other_user_id, dataset_id, chat_id, run_id

    other_user_id, dataset_id, chat_id, run_id = asyncio.run(create_other_tenant_resources())
    try:
        responses = [
            persisted_chat_client.get(f"/api/v1/datasets/{dataset_id}"),
            persisted_chat_client.get(f"/api/v1/datasets/{dataset_id}/columns"),
            persisted_chat_client.get(f"/api/v1/datasets/{dataset_id}/quality-issues"),
            persisted_chat_client.get(f"/api/v1/datasets/{dataset_id}/preview"),
            persisted_chat_client.delete(f"/api/v1/datasets/{dataset_id}"),
            persisted_chat_client.get(f"/api/v1/chats/{chat_id}"),
            persisted_chat_client.patch(f"/api/v1/chats/{chat_id}", json={"title": "No access"}),
            persisted_chat_client.delete(f"/api/v1/chats/{chat_id}"),
            persisted_chat_client.get(f"/api/v1/chats/{chat_id}/messages"),
            persisted_chat_client.post(
                f"/api/v1/chats/{chat_id}/messages",
                json={"content": "No access"},
                headers={"Idempotency-Key": "cross-tenant"},
            ),
            persisted_chat_client.get(f"/api/v1/analysis-runs/{run_id}"),
        ]

        assert all(response.status_code == 404 for response in responses)
        assert all(response.json()["error"]["code"] == "NOT_FOUND" for response in responses)
    finally:
        async def delete_other_user() -> None:
            async with SessionLocal() as session:
                await session.execute(delete(AppUser).where(AppUser.id == other_user_id))
                await session.commit()

        asyncio.run(delete_other_user())
