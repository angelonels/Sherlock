from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class SqlExecutionService:
    async def execute_readonly(self, session: AsyncSession, sql: str) -> dict[str, Any]:
        await session.execute(text("BEGIN READ ONLY"))
        await session.execute(text("SET LOCAL statement_timeout = '10s'"))
        try:
            result = await session.execute(text(sql))
            rows = [dict(row._mapping) for row in result.fetchall()]
            await session.execute(text("ROLLBACK"))
            columns = list(rows[0].keys()) if rows else list(result.keys())
            return {"columns": columns, "rows": rows[:1000], "row_count": len(rows)}
        except Exception:
            await session.execute(text("ROLLBACK"))
            raise
