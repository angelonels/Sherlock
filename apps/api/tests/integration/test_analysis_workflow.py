from __future__ import annotations

import uuid
import re

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select, text

import app.services.ingestion_service as ingestion_module
from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.database import SessionLocal
from app.db.models import AnalysisRun, AppUser, ChatMessage, ChatSession, Dataset, DatasetColumn, DatasetQualityIssue, QueryAttempt, UploadSession
from app.main import app
from app.services.analyst_workflow_service import AnalystWorkflowService
from app.services.job_dispatcher import JobDispatcher
from app.services.maintenance_service import MaintenanceService
from app.services.upload_safety import temp_file_path
from app.workers.analysis_worker import AnalysisWorker
from app.workers.dataset_worker import DatasetWorker


class FakeWorkflowLlm:
    async def complete_json(self, prompt: str) -> dict:
        table_name = self._table_name(prompt)
        question = prompt.split("User question:", 1)[-1].strip().lower()
        if "missing" in question or "quality" in question:
            return {"intent": "quality_question", "query_plans": []}
        if "column" in question or "schema" in question:
            return {"intent": "schema_question", "query_plans": []}
        if "customer" in question and "profit" in question:
            return {
                "intent": "data_question",
                "query_plans": [
                    {
                        "step_index": 1,
                        "purpose": "Top customer_name by profit",
                        "sql": (
                            f'SELECT "customer_name", SUM("profit") AS total_profit '
                            f'FROM user_data."{table_name}" '
                            'GROUP BY "customer_name" ORDER BY total_profit DESC LIMIT 10'
                        ),
                    }
                ],
            }
        return {
            "intent": "data_question",
            "query_plans": [
                {
                    "step_index": 1,
                    "purpose": "Row count",
                    "sql": f'SELECT COUNT(*) AS row_count FROM user_data."{table_name}"',
                }
            ],
        }

    async def complete(self, prompt: str) -> str:
        if "Meera Rao" in prompt:
            return "Meera Rao generated the most total profit, with 55.00."
        if "row_count" in prompt:
            return "The dataset contains 2 rows after duplicate removal."
        return "I analyzed the dataset and prepared the result."

    def _table_name(self, prompt: str) -> str:
        match = re.search(r'physical_table: user_data\."([^"]+)"', prompt)
        assert match
        return match.group(1)


class FailingWorkflow:
    async def run_analysis(self, _session, _run, _settings):
        raise RuntimeError("raw model payload with SELECT secret FROM private and /tmp/secret")


def run_analysis_once() -> int:
    import asyncio

    workflow = AnalystWorkflowService(llm_service=FakeWorkflowLlm())
    return asyncio.run(AnalysisWorker(workflow=workflow).run_once())


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
    assert preview.json()["data"][0]["_sherlock_row_id"]
    assert "_sherlock_row_hash" not in preview.json()["data"][0]
    assert workflow_client.get(f"/api/v1/datasets/{dataset_id}/preview?cursor=invalid").status_code == 422

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

    assert run_analysis_once() >= 1
    run = workflow_client.get(f"/api/v1/analysis-runs/{run_id}").json()["data"]
    assert run["status"] == "success"
    assert run["assistant_message"]["blocks"]
    assert all(block["type"] != "suggestions" for block in run["assistant_message"]["blocks"])

    async def checkpoint_payload() -> dict:
        async with SessionLocal() as session:
            stored_run = await session.get(AnalysisRun, uuid.UUID(run_id))
            assert stored_run is not None
            assert stored_run.checkpoint_thread_id == chat_id
            assert stored_run.checkpoint_run_id == run_id
            result = await session.execute(
                text(
                    """
                    SELECT payload
                    FROM analysis_checkpoints
                    WHERE thread_id = :thread_id AND checkpoint_ns = :checkpoint_ns
                    """
                ),
                {"thread_id": chat_id, "checkpoint_ns": run_id},
            )
            return result.scalar_one()

    checkpoint = asyncio.run(checkpoint_payload())
    assert checkpoint["status"] == "completed"
    assert checkpoint["query_count"] == 1

    updated_chat = workflow_client.get(f"/api/v1/chats/{chat_id}").json()["data"]
    assert updated_chat["title"] == "How many rows are there"


def test_customer_profit_question_returns_top_customer(workflow_client: TestClient) -> None:
    upload = workflow_client.post(
        "/api/v1/upload-sessions",
        files={
            "file": (
                "walmart_sample.csv",
                "customer_name,sales,profit\nAman Sharma,100,15\nMeera Rao,80,55\nAman Sharma,40,10\n",
                "text/csv",
            )
        },
    )
    assert upload.status_code == 201
    upload_id = upload.json()["data"]["id"]

    dataset_response = workflow_client.post("/api/v1/datasets", json={"upload_session_id": upload_id, "name": "Walmart sample"})
    assert dataset_response.status_code == 202
    dataset_id = dataset_response.json()["data"]["id"]

    import asyncio

    assert asyncio.run(DatasetWorker().run_once()) >= 1
    chat = workflow_client.post("/api/v1/chats", json={"dataset_id": dataset_id})
    assert chat.status_code == 201
    chat_id = chat.json()["data"]["id"]

    message = workflow_client.post(
        f"/api/v1/chats/{chat_id}/messages",
        json={"content": "which customer generated the most profit"},
        headers={"Idempotency-Key": "workflow-customer-profit"},
    )
    assert message.status_code == 202
    run_id = message.json()["data"]["analysis_run_id"]

    assert run_analysis_once() >= 1
    run = workflow_client.get(f"/api/v1/analysis-runs/{run_id}").json()["data"]
    content = run["assistant_message"]["content"]
    blocks = run["assistant_message"]["blocks"]
    assert run["status"] == "success"
    assert "Meera Rao" in content
    assert "total profit" in content
    assert any(block["type"] == "table" and block["rows"][0]["customer_name"] == "Meera Rao" for block in blocks)


def test_missing_values_question_prefers_quality_over_schema(workflow_client: TestClient) -> None:
    upload = workflow_client.post(
        "/api/v1/upload-sessions",
        files={
            "file": (
                "quality.csv",
                "region,revenue,profit\nWest,100,10\nEast,,5\nNorth,90,\n",
                "text/csv",
            )
        },
    )
    assert upload.status_code == 201
    upload_id = upload.json()["data"]["id"]

    dataset_response = workflow_client.post("/api/v1/datasets", json={"upload_session_id": upload_id, "name": "Quality sample"})
    assert dataset_response.status_code == 202
    dataset_id = dataset_response.json()["data"]["id"]

    import asyncio

    assert asyncio.run(DatasetWorker().run_once()) >= 1
    chat = workflow_client.post("/api/v1/chats", json={"dataset_id": dataset_id})
    assert chat.status_code == 201
    chat_id = chat.json()["data"]["id"]

    message = workflow_client.post(
        f"/api/v1/chats/{chat_id}/messages",
        json={"content": "what columns have missing values"},
        headers={"Idempotency-Key": "workflow-missing-values"},
    )
    assert message.status_code == 202
    run_id = message.json()["data"]["analysis_run_id"]

    assert run_analysis_once() >= 1
    run = workflow_client.get(f"/api/v1/analysis-runs/{run_id}").json()["data"]
    assistant = run["assistant_message"]
    assert "quality" in assistant["content"].lower()
    assert any(block["type"] == "quality_note" for block in assistant["blocks"])


def test_pii_like_values_warn_without_blocking_ingestion(workflow_client: TestClient) -> None:
    upload = workflow_client.post(
        "/api/v1/upload-sessions",
        files={
            "file": (
                "contacts.csv",
                "customer_email,revenue\naman@example.com,100\nmeera@example.com,150\n",
                "text/csv",
            )
        },
    )
    assert upload.status_code == 201
    upload_id = upload.json()["data"]["id"]

    dataset_response = workflow_client.post("/api/v1/datasets", json={"upload_session_id": upload_id, "name": "Contacts"})
    assert dataset_response.status_code == 202
    dataset_id = dataset_response.json()["data"]["id"]

    import asyncio

    assert asyncio.run(DatasetWorker().run_once()) >= 1
    dataset = workflow_client.get(f"/api/v1/datasets/{dataset_id}").json()["data"]
    issues = workflow_client.get(f"/api/v1/datasets/{dataset_id}/quality-issues").json()["data"]
    columns = workflow_client.get(f"/api/v1/datasets/{dataset_id}/columns").json()["data"]

    assert dataset["status"] == "ready"
    assert any(issue["issue_type"] == "pii_like_values_detected" for issue in issues)
    assert any("pii_like_email_values" in column["warning_flags"] for column in columns)


def test_ingestion_contract_normalizes_nulls_removes_duplicates_cleans_raw_file_and_drops_table(
    workflow_client: TestClient,
) -> None:
    upload = workflow_client.post(
        "/api/v1/upload-sessions",
        files={
            "file": (
                "contract.csv",
                "Region,Revenue\nWest,100\nWest,100\nEast,\n",
                "text/csv",
            )
        },
    )
    assert upload.status_code == 201
    upload_id = upload.json()["data"]["id"]

    async def raw_upload_path():
        async with SessionLocal() as session:
            stored_upload = await session.get(UploadSession, uuid.UUID(upload_id))
            assert stored_upload is not None
            return temp_file_path(get_settings(), stored_upload.temp_file_key)

    import asyncio

    raw_path = asyncio.run(raw_upload_path())
    assert raw_path.exists()

    dataset_response = workflow_client.post(
        "/api/v1/datasets",
        json={"upload_session_id": upload_id, "name": "Ingestion contract"},
    )
    assert dataset_response.status_code == 202
    dataset_id = dataset_response.json()["data"]["id"]
    assert asyncio.run(DatasetWorker().run_once()) >= 1
    assert not raw_path.exists()

    async def physical_contract() -> tuple[str, list[dict], int, int, int]:
        async with SessionLocal() as session:
            dataset = await session.get(Dataset, uuid.UUID(dataset_id))
            assert dataset is not None
            rows = await session.execute(
                text(
                    f'SELECT "region", "revenue", _sherlock_row_hash '
                    f'FROM user_data."{dataset.physical_table_name}" ORDER BY _sherlock_row_id'
                )
            )
            stored_rows = [dict(row._mapping) for row in rows]
            column_count = len(
                (await session.execute(select(DatasetColumn).where(DatasetColumn.dataset_id == dataset.id)))
                .scalars()
                .all()
            )
            issue_count = len(
                (await session.execute(select(DatasetQualityIssue).where(DatasetQualityIssue.dataset_id == dataset.id)))
                .scalars()
                .all()
            )
            return (
                dataset.physical_table_name,
                stored_rows,
                dataset.duplicate_rows_removed,
                column_count,
                issue_count,
            )

    table_name, rows, duplicates_removed, column_count, issue_count = asyncio.run(physical_contract())
    assert rows[0]["region"] == "West"
    assert rows[1]["region"] == "East"
    assert rows[1]["revenue"] is None
    assert len({row["_sherlock_row_hash"] for row in rows}) == 2
    assert duplicates_removed == 1
    assert column_count == 2
    assert issue_count >= 2

    assert workflow_client.delete(f"/api/v1/datasets/{dataset_id}").status_code == 204

    async def physical_table_was_dropped() -> bool:
        async with SessionLocal() as session:
            relation = await session.scalar(
                text("SELECT to_regclass(:qualified_name)"),
                {"qualified_name": f"user_data.{table_name}"},
            )
            return relation is None

    assert asyncio.run(physical_table_was_dropped())


def test_ingestion_failure_exposes_only_user_safe_error(workflow_client: TestClient) -> None:
    upload = workflow_client.post(
        "/api/v1/upload-sessions",
        files={"file": ("broken.csv", "region,revenue\nWest,100\n", "text/csv")},
    )
    assert upload.status_code == 201
    upload_id = upload.json()["data"]["id"]

    async def remove_raw_upload() -> None:
        async with SessionLocal() as session:
            stored_upload = await session.get(UploadSession, uuid.UUID(upload_id))
            assert stored_upload is not None
            temp_file_path(get_settings(), stored_upload.temp_file_key).unlink()

    import asyncio

    asyncio.run(remove_raw_upload())
    dataset_response = workflow_client.post(
        "/api/v1/datasets",
        json={"upload_session_id": upload_id, "name": "Broken ingestion"},
    )
    dataset_id = dataset_response.json()["data"]["id"]

    assert asyncio.run(DatasetWorker().run_once()) >= 1
    dataset = workflow_client.get(f"/api/v1/datasets/{dataset_id}").json()["data"]

    assert dataset["status"] == "failed"
    assert dataset["ingestion_error"] == (
        "Sherlock could not ingest this file. Check the file structure and try a new upload."
    )
    assert "/tmp/" not in dataset["ingestion_error"]


@pytest.mark.enable_background_dispatch
def test_dataset_dispatch_failure_becomes_a_durable_recoverable_failure(
    workflow_client: TestClient,
    monkeypatch,
) -> None:
    upload = workflow_client.post(
        "/api/v1/upload-sessions",
        files={"file": ("dispatch.csv", "region,revenue\nWest,100\n", "text/csv")},
    )
    upload_id = upload.json()["data"]["id"]

    def fail_dispatch(_self, _dataset_id) -> None:
        raise ConnectionError("broker unavailable with internal details")

    monkeypatch.setattr(JobDispatcher, "enqueue_dataset_ingestion", fail_dispatch)
    response = workflow_client.post(
        "/api/v1/datasets",
        json={"upload_session_id": upload_id, "name": "Dispatch failure"},
    )
    dataset = response.json()["data"]

    assert response.status_code == 202
    assert dataset["status"] == "failed"
    assert dataset["ingestion_error"] == "Sherlock could not start ingestion. Try creating the dataset again."
    assert "broker" not in dataset["ingestion_error"]


def test_ingestion_failure_rolls_back_partial_physical_and_metadata_work(
    workflow_client: TestClient,
    monkeypatch,
) -> None:
    upload = workflow_client.post(
        "/api/v1/upload-sessions",
        files={"file": ("rollback.csv", "region,revenue\nWest,100\n", "text/csv")},
    )
    upload_id = upload.json()["data"]["id"]
    dataset_response = workflow_client.post(
        "/api/v1/datasets",
        json={"upload_session_id": upload_id, "name": "Rollback ingestion"},
    )
    dataset_id = dataset_response.json()["data"]["id"]

    async def raw_upload_path():
        async with SessionLocal() as session:
            stored_upload = await session.get(UploadSession, uuid.UUID(upload_id))
            assert stored_upload is not None
            return temp_file_path(get_settings(), stored_upload.temp_file_key)

    async def fail_after_table_creation(*_args, **_kwargs) -> None:
        raise RuntimeError("simulated insert failure with internal details")

    import asyncio

    raw_path = asyncio.run(raw_upload_path())
    worker = DatasetWorker()
    monkeypatch.setattr(worker.ingestion_service, "_insert_rows", fail_after_table_creation)
    assert asyncio.run(worker.run_once()) >= 1

    async def partial_work_was_rolled_back() -> tuple[bool, int, int]:
        async with SessionLocal() as session:
            stored = await session.get(Dataset, uuid.UUID(dataset_id))
            assert stored is not None
            relation = await session.scalar(
                text("SELECT to_regclass(:qualified_name)"),
                {"qualified_name": f"user_data.{stored.physical_table_name}"},
            )
            columns = await session.scalar(
                select(func.count()).select_from(DatasetColumn).where(DatasetColumn.dataset_id == stored.id)
            )
            issues = await session.scalar(
                select(func.count()).select_from(DatasetQualityIssue).where(DatasetQualityIssue.dataset_id == stored.id)
            )
            return relation is None, int(columns or 0), int(issues or 0)

    dataset = workflow_client.get(f"/api/v1/datasets/{dataset_id}").json()["data"]
    assert dataset["status"] == "failed"
    rollback_state = asyncio.run(partial_work_was_rolled_back())
    assert rollback_state == (True, 0, 0)
    assert raw_path.exists()


def test_successful_ingestion_defers_failed_raw_cleanup_and_maintenance_retries(
    workflow_client: TestClient,
    monkeypatch,
) -> None:
    upload = workflow_client.post(
        "/api/v1/upload-sessions",
        files={"file": ("cleanup.csv", "region,revenue\nWest,100\n", "text/csv")},
    )
    upload_id = upload.json()["data"]["id"]
    dataset_id = workflow_client.post(
        "/api/v1/datasets",
        json={"upload_session_id": upload_id, "name": "Deferred cleanup"},
    ).json()["data"]["id"]

    async def raw_upload_path():
        async with SessionLocal() as session:
            stored_upload = await session.get(UploadSession, uuid.UUID(upload_id))
            assert stored_upload is not None
            return temp_file_path(get_settings(), stored_upload.temp_file_key)

    def fail_cleanup(*_args, **_kwargs) -> None:
        raise PermissionError("simulated cleanup failure")

    import asyncio

    raw_path = asyncio.run(raw_upload_path())
    original_cleanup = ingestion_module.delete_temp_file
    monkeypatch.setattr(ingestion_module, "delete_temp_file", fail_cleanup)
    assert asyncio.run(DatasetWorker().run_once()) >= 1

    async def cleanup_state() -> tuple[str, bool]:
        async with SessionLocal() as session:
            dataset = await session.get(Dataset, uuid.UUID(dataset_id))
            assert dataset is not None
            return dataset.status, dataset.raw_file_deleted_at is None

    assert asyncio.run(cleanup_state()) == ("ready", True)
    assert raw_path.exists()

    monkeypatch.setattr(ingestion_module, "delete_temp_file", original_cleanup)

    async def run_maintenance() -> tuple[int, bool]:
        async with SessionLocal() as session:
            count = await MaintenanceService().cleanup_ingested_upload_files(session, get_settings())
            dataset = await session.get(Dataset, uuid.UUID(dataset_id))
            assert dataset is not None
            return count, dataset.raw_file_deleted_at is not None

    cleaned_count, marked_deleted = asyncio.run(run_maintenance())
    assert cleaned_count >= 1
    assert marked_deleted is True
    assert not raw_path.exists()


def test_analysis_failure_exposes_only_user_safe_error(workflow_client: TestClient) -> None:
    upload = workflow_client.post(
        "/api/v1/upload-sessions",
        files={"file": ("safe-failure.csv", "region,revenue\nWest,100\n", "text/csv")},
    )
    upload_id = upload.json()["data"]["id"]
    dataset_response = workflow_client.post(
        "/api/v1/datasets",
        json={"upload_session_id": upload_id, "name": "Safe failure"},
    )
    dataset_id = dataset_response.json()["data"]["id"]

    import asyncio

    assert asyncio.run(DatasetWorker().run_once()) >= 1
    chat_id = workflow_client.post("/api/v1/chats", json={"dataset_id": dataset_id}).json()["data"]["id"]
    message = workflow_client.post(
        f"/api/v1/chats/{chat_id}/messages",
        json={"content": "Trigger a malformed model response"},
        headers={"Idempotency-Key": "safe-analysis-failure"},
    )
    run_id = message.json()["data"]["analysis_run_id"]

    assert asyncio.run(AnalysisWorker(workflow=FailingWorkflow()).run_once()) >= 1
    run = workflow_client.get(f"/api/v1/analysis-runs/{run_id}").json()["data"]

    assert run["status"] == "failed"
    assert run["error_code"] == "ANALYSIS_WORKFLOW_FAILED"
    assert run["error_message"] == (
        "Sherlock could not complete this analysis. Try rephrasing the question or asking a narrower question."
    )
    assert "SELECT" not in run["error_message"]
    assert "/tmp/" not in run["error_message"]
