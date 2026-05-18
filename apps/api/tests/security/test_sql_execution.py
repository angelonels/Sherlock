from __future__ import annotations

import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.core.database import SessionLocal, engine
from app.services.sql_execution_service import SqlExecutionService


@pytest.mark.asyncio
async def test_sql_execution_runs_in_readonly_transaction_and_rolls_back() -> None:
    table_name = f"readonly_contract_{uuid.uuid4().hex}"
    qualified_table = f'user_data."{table_name}"'

    async with SessionLocal() as session:
        await session.execute(text("CREATE SCHEMA IF NOT EXISTS user_data"))
        await session.execute(text(f"CREATE TABLE {qualified_table} (value INTEGER NOT NULL)"))
        await session.execute(text(f"INSERT INTO {qualified_table} (value) VALUES (7)"))
        await session.commit()

        try:
            result = await SqlExecutionService(engine).execute_readonly(
                session,
                f"SELECT value FROM {qualified_table}",
            )

            assert result == {"columns": ["value"], "rows": [{"value": 7}], "row_count": 1}

            with pytest.raises(DBAPIError):
                await SqlExecutionService(engine).execute_readonly(
                    session,
                    f"INSERT INTO {qualified_table} (value) VALUES (8)",
                )

            count = await session.scalar(text(f"SELECT COUNT(*) FROM {qualified_table}"))
            assert count == 1
        finally:
            await session.execute(text(f"DROP TABLE IF EXISTS {qualified_table}"))
            await session.commit()
