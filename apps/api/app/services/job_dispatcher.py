from __future__ import annotations

import uuid


PUBLISH_RETRY_POLICY = {
    "max_retries": 3,
    "interval_start": 0,
    "interval_step": 0.5,
    "interval_max": 1,
}


class JobDispatcher:
    """Small seam for background dispatch so routes/services do not import Celery directly."""

    def enqueue_dataset_ingestion(self, dataset_id: uuid.UUID) -> None:
        from app.workers.tasks import ingest_dataset

        ingest_dataset.apply_async(args=[str(dataset_id)], retry=True, retry_policy=PUBLISH_RETRY_POLICY)

    def enqueue_analysis_run(self, analysis_run_id: uuid.UUID) -> None:
        from app.workers.tasks import run_analysis

        run_analysis.apply_async(args=[str(analysis_run_id)], retry=True, retry_policy=PUBLISH_RETRY_POLICY)
