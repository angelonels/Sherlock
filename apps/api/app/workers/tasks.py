from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import UTC, datetime
from time import perf_counter

from botocore.exceptions import BotoCoreError
from sqlalchemy.exc import OperationalError

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.db.models import AnalysisRun, Dataset
from app.services.analyst_workflow_service import AnalystWorkflowService
from app.services.ingestion_service import IngestionService
from app.services.maintenance_service import MaintenanceService
from app.workers.celery_app import celery_app


logger = logging.getLogger("sherlock.worker")
TRANSIENT_WORKER_ERRORS = (OperationalError, ConnectionError, TimeoutError, BotoCoreError)


def _run(coro):
    return asyncio.run(coro)


@celery_app.task(
    bind=True,
    name="app.workers.tasks.ingest_dataset",
    autoretry_for=TRANSIENT_WORKER_ERRORS,
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def ingest_dataset(self, dataset_id: str) -> dict[str, str | int | None]:
    return _run(_ingest_dataset(dataset_id, celery_task_id=self.request.id))


async def _ingest_dataset(dataset_id: str, *, celery_task_id: str | None = None) -> dict[str, str | int | None]:
    settings = get_settings()
    started = perf_counter()
    async with SessionLocal() as session:
        dataset = await session.get(Dataset, uuid.UUID(dataset_id))
        if not dataset or dataset.deleted_at is not None:
            return {"dataset_id": dataset_id, "status": "skipped", "duration_ms": 0}
        if dataset.status != "processing":
            return {"dataset_id": dataset_id, "status": dataset.status, "duration_ms": 0}

        logger.info(
            "ingest_dataset started",
            extra={"job_name": "ingest_dataset", "celery_task_id": celery_task_id, "dataset_id": dataset_id},
        )
        result = await IngestionService().ingest_dataset(session, dataset, settings)
        duration_ms = int((perf_counter() - started) * 1000)
        logger.info(
            "ingest_dataset finished",
            extra={
                "job_name": "ingest_dataset",
                "celery_task_id": celery_task_id,
                "user_id": str(result.user_id),
                "dataset_id": dataset_id,
                "status": result.status,
                "duration_ms": duration_ms,
                "error_code": "DATASET_INGESTION_FAILED" if result.status == "failed" else None,
            },
        )
        return {"dataset_id": dataset_id, "status": result.status, "duration_ms": duration_ms}


@celery_app.task(
    bind=True,
    name="app.workers.tasks.run_analysis",
    autoretry_for=TRANSIENT_WORKER_ERRORS,
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def run_analysis(self, analysis_run_id: str) -> dict[str, str | int | None]:
    return _run(_run_analysis(analysis_run_id, celery_task_id=self.request.id))


async def _run_analysis(analysis_run_id: str, *, celery_task_id: str | None = None) -> dict[str, str | int | None]:
    settings = get_settings()
    workflow = AnalystWorkflowService()
    started = perf_counter()
    async with SessionLocal() as session:
        analysis_run = await session.get(AnalysisRun, uuid.UUID(analysis_run_id))
        if not analysis_run:
            return {"analysis_run_id": analysis_run_id, "status": "skipped", "duration_ms": 0}
        if analysis_run.status != "queued":
            return {"analysis_run_id": analysis_run_id, "status": analysis_run.status, "duration_ms": 0}

        logger.info(
            "run_analysis started",
            extra={
                "job_name": "run_analysis",
                "celery_task_id": celery_task_id,
                "chat_id": str(analysis_run.chat_session_id),
                "analysis_run_id": analysis_run_id,
                "stage": analysis_run.current_stage,
                "status": analysis_run.status,
            },
        )
        try:
            result = await workflow.run_analysis(session, analysis_run, settings)
        except Exception as exc:
            await session.rollback()
            if isinstance(exc, TRANSIENT_WORKER_ERRORS):
                logger.exception(
                    "run_analysis transient failure; retrying",
                    extra={
                        "job_name": "run_analysis",
                        "celery_task_id": celery_task_id,
                        "analysis_run_id": analysis_run_id,
                        "error_code": "TRANSIENT_ANALYSIS_FAILURE",
                    },
                )
                raise
            failed = await session.get(AnalysisRun, uuid.UUID(analysis_run_id))
            if failed and failed.status in {"queued", "running"}:
                failed.status = "failed"
                failed.current_stage = "failed"
                failed.error_code = "ANALYSIS_WORKFLOW_FAILED"
                failed.error_message = "Sherlock could not complete this analysis. Try rephrasing the question or asking a narrower question."
                failed.completed_at = datetime.now(UTC)
                await session.commit()
            logger.exception(
                "run_analysis failed",
                extra={
                    "job_name": "run_analysis",
                    "celery_task_id": celery_task_id,
                    "analysis_run_id": analysis_run_id,
                    "error_code": "ANALYSIS_WORKFLOW_FAILED",
                },
            )
            return {
                "analysis_run_id": analysis_run_id,
                "status": "failed",
                "duration_ms": int((perf_counter() - started) * 1000),
            }

        duration_ms = int((perf_counter() - started) * 1000)
        logger.info(
            "run_analysis finished",
            extra={
                "job_name": "run_analysis",
                "celery_task_id": celery_task_id,
                "chat_id": str(result.chat_session_id),
                "analysis_run_id": analysis_run_id,
                "stage": result.current_stage,
                "status": result.status,
                "duration_ms": duration_ms,
                "error_code": result.error_code,
            },
        )
        return {"analysis_run_id": analysis_run_id, "status": result.status, "duration_ms": duration_ms}


@celery_app.task(name="app.workers.tasks.cleanup_expired_upload_sessions")
def cleanup_expired_upload_sessions() -> int:
    return _run(_cleanup_expired_upload_sessions())


async def _cleanup_expired_upload_sessions() -> int:
    async with SessionLocal() as session:
        return await MaintenanceService().cleanup_expired_upload_sessions(session, get_settings())


@celery_app.task(name="app.workers.tasks.cleanup_ingested_upload_files")
def cleanup_ingested_upload_files() -> int:
    return _run(_cleanup_ingested_upload_files())


async def _cleanup_ingested_upload_files() -> int:
    async with SessionLocal() as session:
        return await MaintenanceService().cleanup_ingested_upload_files(session, get_settings())


@celery_app.task(name="app.workers.tasks.fail_stuck_analysis_runs")
def fail_stuck_analysis_runs() -> int:
    return _run(_fail_stuck_analysis_runs())


async def _fail_stuck_analysis_runs() -> int:
    async with SessionLocal() as session:
        return await MaintenanceService().fail_stuck_analysis_runs(session)
