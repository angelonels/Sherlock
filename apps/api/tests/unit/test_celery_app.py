from __future__ import annotations

from botocore.exceptions import BotoCoreError
from sqlalchemy.exc import OperationalError

from app.workers.celery_app import celery_app
from app.workers.tasks import TRANSIENT_WORKER_ERRORS


def test_celery_app_registers_required_tasks_and_maintenance_schedule() -> None:
    celery_app.loader.import_default_modules()

    assert "app.workers.tasks.ingest_dataset" in celery_app.tasks
    assert "app.workers.tasks.run_analysis" in celery_app.tasks
    assert "app.workers.tasks.cleanup_expired_upload_sessions" in celery_app.tasks
    assert "app.workers.tasks.cleanup_ingested_upload_files" in celery_app.tasks
    assert "app.workers.tasks.fail_stuck_analysis_runs" in celery_app.tasks
    assert set(celery_app.conf.beat_schedule) == {
        "cleanup-expired-upload-sessions",
        "cleanup-ingested-upload-files",
        "fail-stuck-analysis-runs",
    }
    assert celery_app.conf.task_acks_late is True
    assert celery_app.conf.task_reject_on_worker_lost is True


def test_worker_retry_policy_includes_transient_database_bedrock_and_transport_errors() -> None:
    assert OperationalError in TRANSIENT_WORKER_ERRORS
    assert BotoCoreError in TRANSIENT_WORKER_ERRORS
    assert ConnectionError in TRANSIENT_WORKER_ERRORS
    assert TimeoutError in TRANSIENT_WORKER_ERRORS
