from __future__ import annotations

from app.services.llm_service import LlmService
from app.services.prompt_service import PromptService


class SqlRepairService:
    """Repair one failed read-only SQL candidate; validation remains authoritative."""

    def __init__(
        self,
        *,
        llm_service: LlmService | None = None,
        prompt_service: PromptService | None = None,
    ) -> None:
        self.llm_service = llm_service or LlmService()
        self.prompt_service = prompt_service or PromptService()

    async def repair(
        self,
        sql: str,
        *,
        error: str,
        table_name: str,
        allowed_columns: set[str],
    ) -> str | None:
        prompt = self.prompt_service.sql_repair_prompt(
            sql=sql,
            error=error,
            table_name=table_name,
            allowed_columns=allowed_columns,
        )
        try:
            payload = await self.llm_service.complete_json(prompt)
        except Exception:
            return None
        repaired_sql = str(payload.get("sql") or "").strip()
        if not repaired_sql or repaired_sql == sql.strip():
            return None
        return repaired_sql
