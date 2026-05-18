from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.core.database import readonly_engine


class SqlExecutionService:
    def __init__(self, execution_engine: AsyncEngine | None = None) -> None:
        self.execution_engine = execution_engine or readonly_engine

    async def execute_readonly(self, session: AsyncSession, sql: str) -> dict[str, Any]:
        _ = session
        async with self.execution_engine.connect() as connection:
            transaction = await connection.begin()
            try:
                await connection.execute(text("SET TRANSACTION READ ONLY"))
                await connection.execute(text("SET LOCAL statement_timeout = '10s'"))
                result = await connection.execute(text(sql))
                rows = [{key: self._json_safe(value) for key, value in row._mapping.items()} for row in result.fetchall()]
                columns = list(rows[0].keys()) if rows else list(result.keys())
                return {"columns": columns, "rows": rows[:1000], "row_count": len(rows)}
            finally:
                await transaction.rollback()

    def _json_safe(self, value: Any) -> Any:
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, (date, datetime)):
            return value.isoformat()
        return value
