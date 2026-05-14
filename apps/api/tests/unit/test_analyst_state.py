from __future__ import annotations

from typing import get_args, get_origin, get_type_hints

from sqlalchemy.orm import DeclarativeBase

from app.agents.graph import AnalystGraph
from app.agents.models import DatasetContext, QueryResultSummary
from app.agents.state import AnalystState
from app.core.config import Settings


def _contains_sqlalchemy_model(annotation: object) -> bool:
    origin = get_origin(annotation)
    if origin:
        return any(_contains_sqlalchemy_model(arg) for arg in get_args(annotation))
    return isinstance(annotation, type) and issubclass(annotation, DeclarativeBase)


def test_analyst_state_does_not_checkpoint_orm_models() -> None:
    annotations = get_type_hints(AnalystState)

    assert not {
        name
        for name, annotation in annotations.items()
        if _contains_sqlalchemy_model(annotation)
    }


async def test_query_failure_block_does_not_expose_internal_error_details() -> None:
    class FakeSession:
        async def flush(self) -> None:
            return None

    class FakeRun:
        current_stage = None

    graph = AnalystGraph()
    graph._runtime = lambda _config: (FakeSession(), FakeRun(), Settings(_env_file=None, app_env="production"))
    state: AnalystState = {
        "dataset": DatasetContext(
            id="dataset_1",
            name="Sales",
            physical_schema_name="user_data",
            physical_table_name="dataset_1",
            row_count=2,
            column_count=2,
        ),
        "content": "The analysis query could not be run safely.",
        "query_results": [],
        "query_failures": [
            QueryResultSummary(
                step_index=1,
                purpose="Unsafe query",
                status="failed",
                sql='SELECT secret FROM public.private_table',
                error="raw database error from /tmp/secret",
            )
        ],
    }

    result = await graph.build_blocks(state, {"metadata": {}})
    serialized = str(result["blocks"])

    assert "raw database error" not in serialized
    assert "/tmp/secret" not in serialized
    assert "SELECT secret" not in serialized
    assert "Try rephrasing" in serialized
