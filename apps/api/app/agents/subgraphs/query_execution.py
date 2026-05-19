from __future__ import annotations

import inspect

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.models import QueryPlan, QueryResultSummary
from app.db.models import DatasetColumn, QueryAttempt
from app.services.sql_repair_service import SqlRepairService
from app.services.sql_execution_service import SqlExecutionService
from app.services.sql_validation_service import SqlValidationService


class QueryExecutionSubgraph:
    def __init__(
        self,
        *,
        validator: SqlValidationService | None = None,
        executor: SqlExecutionService | None = None,
        repair_service: object | None = None,
        max_repair_attempts: int = 2,
    ) -> None:
        self.validator = validator or SqlValidationService()
        self.executor = executor or SqlExecutionService()
        self.repair_service = repair_service or SqlRepairService()
        self.max_repair_attempts = max_repair_attempts

    async def run(
        self,
        session: AsyncSession,
        *,
        dataset_id,
        physical_table_name: str,
        analysis_run_id,
        plan: QueryPlan,
    ) -> QueryResultSummary:
        columns_result = await session.execute(select(DatasetColumn.column_name).where(DatasetColumn.dataset_id == dataset_id))
        allowed_columns = set(columns_result.scalars().all())
        candidate_sql = plan.sql
        last_error = None
        repair_reason = None

        for attempt_number in range(1, self.max_repair_attempts + 2):
            validation = self.validator.validate(candidate_sql, table_name=physical_table_name, allowed_columns=allowed_columns)
            if not validation.is_valid:
                last_error = validation.error
                await self._record_attempt(
                    session,
                    analysis_run_id=analysis_run_id,
                    step_index=plan.step_index,
                    purpose=plan.purpose,
                    attempt_number=attempt_number,
                    generated_sql=candidate_sql,
                    validation_status="invalid",
                    execution_status="not_run",
                    repair_reason=repair_reason,
                    error_message=last_error,
                )
                if attempt_number > self.max_repair_attempts:
                    break
                repaired_sql = await self._repair(
                    candidate_sql,
                    error=last_error or "SQL validation failed.",
                    table_name=physical_table_name,
                    allowed_columns=allowed_columns,
                )
                if not repaired_sql:
                    break
                candidate_sql = repaired_sql
                repair_reason = last_error
                continue

            try:
                result = await self.executor.execute_readonly(session, validation.sql or candidate_sql)
                await self._record_attempt(
                    session,
                    analysis_run_id=analysis_run_id,
                    step_index=plan.step_index,
                    purpose=plan.purpose,
                    attempt_number=attempt_number,
                    generated_sql=candidate_sql,
                    validated_sql=validation.sql,
                    validation_status="valid",
                    execution_status="success",
                    repair_reason=repair_reason,
                    row_count=result["row_count"],
                    result_columns=result["columns"],
                    result_preview=result["rows"][:25],
                    result_summary={"row_count": result["row_count"]},
                )
                return QueryResultSummary(
                    step_index=plan.step_index,
                    purpose=plan.purpose,
                    status="success",
                    sql=validation.sql,
                    columns=result["columns"],
                    rows=result["rows"][:25],
                    row_count=result["row_count"],
                )
            except Exception as exc:
                last_error = str(exc)
                await self._record_attempt(
                    session,
                    analysis_run_id=analysis_run_id,
                    step_index=plan.step_index,
                    purpose=plan.purpose,
                    attempt_number=attempt_number,
                    generated_sql=candidate_sql,
                    validated_sql=validation.sql,
                    validation_status="valid",
                    execution_status="failed",
                    repair_reason=repair_reason,
                    error_message=last_error,
                )
                if attempt_number > self.max_repair_attempts:
                    break
                repaired_sql = await self._repair(
                    candidate_sql,
                    error=last_error,
                    table_name=physical_table_name,
                    allowed_columns=allowed_columns,
                )
                if not repaired_sql:
                    break
                candidate_sql = repaired_sql
                repair_reason = last_error

        return QueryResultSummary(step_index=plan.step_index, purpose=plan.purpose, status="failed", sql=candidate_sql, error=last_error)

    async def _repair(self, sql: str, *, error: str, table_name: str, allowed_columns: set[str]) -> str | None:
        if self.repair_service and hasattr(self.repair_service, "repair"):
            result = self.repair_service.repair(
                sql,
                error=error,
                table_name=table_name,
                allowed_columns=allowed_columns,
            )
            if inspect.isawaitable(result):
                return await result
            return result
        return None

    async def _record_attempt(self, session: AsyncSession, **values) -> None:
        stmt = insert(QueryAttempt).values(**values)
        stmt = stmt.on_conflict_do_nothing(index_elements=["analysis_run_id", "step_index", "attempt_number"])
        await session.execute(stmt)
        await session.flush()
