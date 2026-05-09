from __future__ import annotations

from celery import Celery

from app.core.config import get_settings


def create_celery_app() -> Celery:
    settings = get_settings()
    app = Celery(
        "sherlock",
        broker=settings.effective_celery_broker_url,
        backend=settings.effective_celery_result_backend,
        include=["app.workers.tasks"],
    )
    app.conf.update(
        task_always_eager=settings.celery_task_always_eager,
        task_eager_propagates=settings.celery_task_eager_propagates,
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        worker_prefetch_multiplier=1,
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="UTC",
        beat_schedule={
            "cleanup-expired-upload-sessions": {
                "task": "app.workers.tasks.cleanup_expired_upload_sessions",
                "schedule": 300.0,
            },
            "cleanup-ingested-upload-files": {
                "task": "app.workers.tasks.cleanup_ingested_upload_files",
                "schedule": 300.0,
            },
            "fail-stuck-analysis-runs": {
                "task": "app.workers.tasks.fail_stuck_analysis_runs",
                "schedule": 300.0,
            },
        },
    )
    return app


celery_app = create_celery_app()
