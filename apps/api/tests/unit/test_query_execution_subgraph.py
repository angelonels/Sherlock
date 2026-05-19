from __future__ import annotations

import uuid

import pytest

from app.agents.models import QueryPlan
from app.agents.subgraphs.query_execution import QueryExecutionSubgraph


class _ScalarResult:
    def __init__(self, values: list[str]) -> None:
        self.values = values

    def all(self) -> list[str]:
        return self.values


class _ExecuteResult:
    def __init__(self, values: list[str]) -> None:
        self.values = values

    def scalars(self) -> _ScalarResult:
        return _ScalarResult(self.values)


class _FakeSession:
    async def execute(self, _statement):
        return _ExecuteResult(["region"])

    async def flush(self) -> None:
        return None


class _FakeExecutor:
    async def execute_readonly(self, _session, sql: str) -> dict:
        assert '"region"' in sql
        return {"columns": ["region"], "rows": [{"region": "West"}], "row_count": 1}


class _RepairOnce:
    async def repair(self, _sql: str, *, error: str, table_name: str, allowed_columns: set[str]) -> str:
        assert "Unknown or unauthorized column" in error
        assert table_name == "dataset_1"
        assert allowed_columns == {"region"}
        return 'SELECT "region" FROM user_data."dataset_1"'


class _AlwaysInvalidRepair:
    def __init__(self) -> None:
        self.count = 0

    async def repair(self, _sql: str, **_kwargs) -> str:
        self.count += 1
        return f'SELECT "missing_{self.count}" FROM user_data."dataset_1"'


class _RecordingQueryExecutionSubgraph(QueryExecutionSubgraph):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.attempts: list[dict] = []

    async def _record_attempt(self, _session, **values) -> None:
        self.attempts.append(values)


@pytest.mark.asyncio
async def test_query_execution_repairs_invalid_sql_and_records_repair_reason() -> None:
    subgraph = _RecordingQueryExecutionSubgraph(
        executor=_FakeExecutor(),
        repair_service=_RepairOnce(),
    )

    result = await subgraph.run(
        _FakeSession(),
        dataset_id=uuid.uuid4(),
        physical_table_name="dataset_1",
        analysis_run_id=uuid.uuid4(),
        plan=QueryPlan(step_index=1, purpose="Region list", sql='SELECT "missing" FROM user_data."dataset_1"'),
    )

    assert result.status == "success"
    assert result.rows == [{"region": "West"}]
    assert [attempt["validation_status"] for attempt in subgraph.attempts] == ["invalid", "valid"]
    assert subgraph.attempts[0]["repair_reason"] is None
    assert "Unknown or unauthorized column" in subgraph.attempts[1]["repair_reason"]


@pytest.mark.asyncio
async def test_query_execution_caps_sql_repair_attempts() -> None:
    repair = _AlwaysInvalidRepair()
    subgraph = _RecordingQueryExecutionSubgraph(
        executor=_FakeExecutor(),
        repair_service=repair,
        max_repair_attempts=2,
    )

    result = await subgraph.run(
        _FakeSession(),
        dataset_id=uuid.uuid4(),
        physical_table_name="dataset_1",
        analysis_run_id=uuid.uuid4(),
        plan=QueryPlan(step_index=1, purpose="Region list", sql='SELECT "missing_0" FROM user_data."dataset_1"'),
    )

    assert result.status == "failed"
    assert repair.count == 2
    assert len(subgraph.attempts) == 3
    assert all(attempt["validation_status"] == "invalid" for attempt in subgraph.attempts)
