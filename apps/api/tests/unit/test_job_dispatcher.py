from __future__ import annotations

import uuid

import pytest

from app.services.job_dispatcher import JobDispatcher


@pytest.mark.enable_background_dispatch
def test_job_dispatcher_enqueues_dataset_ingestion(monkeypatch) -> None:
    calls: list[dict[str, object]] = []

    from app.workers import tasks

    monkeypatch.setattr(tasks.ingest_dataset, "apply_async", lambda **kwargs: calls.append(kwargs))

    dataset_id = uuid.uuid4()
    JobDispatcher().enqueue_dataset_ingestion(dataset_id)

    assert calls == [
        {
            "args": [str(dataset_id)],
            "retry": True,
            "retry_policy": {
                "max_retries": 3,
                "interval_start": 0,
                "interval_step": 0.5,
                "interval_max": 1,
            },
        }
    ]


@pytest.mark.enable_background_dispatch
def test_job_dispatcher_enqueues_analysis_run(monkeypatch) -> None:
    calls: list[dict[str, object]] = []

    from app.workers import tasks

    monkeypatch.setattr(tasks.run_analysis, "apply_async", lambda **kwargs: calls.append(kwargs))

    analysis_run_id = uuid.uuid4()
    JobDispatcher().enqueue_analysis_run(analysis_run_id)

    assert calls == [
        {
            "args": [str(analysis_run_id)],
            "retry": True,
            "retry_policy": {
                "max_retries": 3,
                "interval_start": 0,
                "interval_step": 0.5,
                "interval_max": 1,
            },
        }
    ]
