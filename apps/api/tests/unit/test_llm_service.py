from __future__ import annotations

import threading

import pytest

from app.core.config import Settings
from app.services.llm_service import LlmService


@pytest.mark.asyncio
async def test_complete_runs_blocking_bedrock_call_off_event_loop(monkeypatch) -> None:
    service = LlmService(Settings(_env_file=None))
    caller_thread = threading.get_ident()
    worker_threads: list[int] = []

    def fake_complete_sync(prompt: str) -> str:
        worker_threads.append(threading.get_ident())
        return f"answer:{prompt}"

    monkeypatch.setattr(service, "_complete_sync", fake_complete_sync)

    assert await service.complete("question") == "answer:question"
    assert worker_threads
    assert worker_threads[0] != caller_thread


@pytest.mark.asyncio
async def test_complete_json_accepts_fenced_json(monkeypatch) -> None:
    service = LlmService(Settings(_env_file=None))

    async def fake_complete(_prompt: str) -> str:
        return '```json\n{"intent":"quality_question","query_plans":[]}\n```'

    monkeypatch.setattr(service, "complete", fake_complete)

    assert await service.complete_json("plan") == {
        "intent": "quality_question",
        "query_plans": [],
    }


def test_bedrock_request_requires_credentials() -> None:
    service = LlmService(Settings(_env_file=None, aws_access_key_id=None, aws_secret_access_key=None))

    with pytest.raises(RuntimeError, match="credentials are not configured"):
        service._complete_sync("question")
