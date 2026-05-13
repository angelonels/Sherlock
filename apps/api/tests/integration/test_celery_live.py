from __future__ import annotations

import asyncio
import os
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import delete

from app.core.database import SessionLocal
from app.db.models import AnalysisRun, AppUser, ChatMessage, ChatSession, Dataset
from app.workers.celery_app import celery_app


pytestmark = [
    pytest.mark.live_celery,
    pytest.mark.skipif(
        os.getenv("RUN_LIVE_CELERY_TESTS") != "1",
        reason="Set RUN_LIVE_CELERY_TESTS=1 and start a Celery worker to run live broker tests.",
    ),
]


def test_live_worker_routes_tasks_through_redis_and_skips_missing_resources() -> None:
    dataset_id = str(uuid.uuid4())
    analysis_run_id = str(uuid.uuid4())

    ingest_result = celery_app.send_task("app.workers.tasks.ingest_dataset", args=[dataset_id])
    analysis_result = celery_app.send_task("app.workers.tasks.run_analysis", args=[analysis_run_id])

    assert ingest_result.get(timeout=20, disable_sync_subtasks=False) == {
        "dataset_id": dataset_id,
        "status": "skipped",
        "duration_ms": 0,
    }
    assert analysis_result.get(timeout=20, disable_sync_subtasks=False) == {
        "analysis_run_id": analysis_run_id,
        "status": "skipped",
        "duration_ms": 0,
    }


def test_live_maintenance_task_recovers_stuck_analysis_run() -> None:
    user_id, run_id = asyncio.run(_create_stuck_analysis_run())
    try:
        result = celery_app.send_task("app.workers.tasks.fail_stuck_analysis_runs")

        assert result.get(timeout=20, disable_sync_subtasks=False) >= 1
        assert asyncio.run(_analysis_status(run_id)) == ("failed", "failed", "STUCK_RUN")
    finally:
        asyncio.run(_delete_user(user_id))


async def _create_stuck_analysis_run() -> tuple[uuid.UUID, uuid.UUID]:
    user_id = uuid.uuid4()
    dataset_id = uuid.uuid4()
    chat_id = uuid.uuid4()
    message_id = uuid.uuid4()
    run_id = uuid.uuid4()
    user = AppUser(id=user_id, clerk_user_id=f"live_celery_{uuid.uuid4().hex}", email="live-celery@example.com")
    dataset = Dataset(
        id=dataset_id,
        user_id=user_id,
        name="Live Celery recovery",
        source_file_type="csv",
        physical_table_name=f"dataset_{uuid.uuid4().hex}",
        status="locked",
    )
    chat = ChatSession(id=chat_id, user_id=user_id, dataset_id=dataset_id, title="Recovery test")
    message = ChatMessage(
        id=message_id,
        chat_session_id=chat_id,
        message_index=1,
        client_message_id=f"live-{uuid.uuid4().hex}",
        idempotency_body_hash="live",
        role="user",
        content="Recover this run",
    )
    run = AnalysisRun(
        id=run_id,
        chat_session_id=chat_id,
        user_message_id=message_id,
        status="running",
        current_stage="querying",
        started_at=datetime.now(UTC) - timedelta(hours=1),
    )
    async with SessionLocal() as session:
        session.add(user)
        await session.flush()
        session.add(dataset)
        await session.flush()
        session.add(chat)
        await session.flush()
        session.add(message)
        await session.flush()
        session.add(run)
        await session.commit()
        return user_id, run_id


async def _analysis_status(run_id: uuid.UUID) -> tuple[str, str | None, str | None]:
    async with SessionLocal() as session:
        run = await session.get(AnalysisRun, run_id)
        assert run is not None
        return run.status, run.current_stage, run.error_code


async def _delete_user(user_id: uuid.UUID) -> None:
    async with SessionLocal() as session:
        await session.execute(delete(AppUser).where(AppUser.id == user_id))
        await session.commit()
