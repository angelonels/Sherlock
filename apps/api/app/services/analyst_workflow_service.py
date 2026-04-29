from __future__ import annotations

import time
from datetime import UTC, datetime

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.models import QueryPlan, QueryResultSummary
from app.agents.subgraphs.query_execution import QueryExecutionSubgraph
from app.core.config import Settings
from app.db.models import AnalysisRun, ChatMessage, ChatSession, Dataset, DatasetColumn, DatasetQualityIssue
from app.services.block_service import BlockService
from app.services.sql_generation_service import SqlGenerationService


class AnalystWorkflowService:
    def __init__(self) -> None:
        self.block_service = BlockService()
        self.query_subgraph = QueryExecutionSubgraph()
        self.sql_generation = SqlGenerationService()

    async def run_analysis(self, session: AsyncSession, analysis_run: AnalysisRun, settings: Settings) -> AnalysisRun:
        started = time.perf_counter()
        if analysis_run.assistant_message_id:
            return analysis_run

        analysis_run.status = "running"
        analysis_run.current_stage = "loading_context"
        analysis_run.started_at = datetime.now(UTC)
        await session.flush()

        user_message = await session.get(ChatMessage, analysis_run.user_message_id)
        chat = await session.get(ChatSession, analysis_run.chat_session_id)
        dataset = await session.get(Dataset, chat.dataset_id)
        question = (user_message.content or "").strip()

        analysis_run.current_stage = "planning"
        intent = self._classify(question)
        analysis_run.intent = intent
        plans = await self._plans(session, dataset, question, intent)
        analysis_run.planner_output = {"query_plans": [plan.model_dump() for plan in plans]}
        await session.flush()

        results: list[QueryResultSummary] = []
        failures: list[QueryResultSummary] = []
        if plans:
            analysis_run.current_stage = "querying"
            for plan in plans[:5]:
                result = await self.query_subgraph.run(session, dataset=dataset, analysis_run_id=analysis_run.id, plan=plan)
                (results if result.status == "success" else failures).append(result)

        analysis_run.current_stage = "synthesizing"
        content, blocks = await self._answer(session, dataset, question, intent, results, settings)
        analysis_run.current_stage = "building_response"
        assistant = await self._persist_assistant(session, analysis_run, content, blocks)
        analysis_run.assistant_message_id = assistant.id
        analysis_run.status = "partial_success" if failures and results else "success"
        analysis_run.current_stage = "completed"
        analysis_run.completed_at = datetime.now(UTC)
        analysis_run.total_duration_ms = int((time.perf_counter() - started) * 1000)
        analysis_run.graph_trace = {"query_results": [result.model_dump() for result in results], "query_failures": [result.model_dump() for result in failures]}
        analysis_run.checkpoint_thread_id = str(analysis_run.chat_session_id)
        analysis_run.checkpoint_run_id = str(analysis_run.id)
        await self._checkpoint(session, analysis_run)
        await session.commit()
        await session.refresh(analysis_run)
        return analysis_run

    def _classify(self, question: str) -> str:
        lowered = question.lower()
        if "column" in lowered or "schema" in lowered:
            return "schema_question"
        if "missing" in lowered or "quality" in lowered:
            return "quality_question"
        if "summar" in lowered:
            return "summary_question"
        return "data_question"

    async def _plans(self, session: AsyncSession, dataset: Dataset, question: str, intent: str) -> list[QueryPlan]:
        lowered = question.lower()
        if intent in {"schema_question", "quality_question"}:
            return []
        if "how many" in lowered or "count" in lowered or "row" in lowered or intent == "summary_question":
            return [self.sql_generation.row_count_plan(dataset.physical_table_name)]
        columns = await session.execute(select(DatasetColumn).where(DatasetColumn.dataset_id == dataset.id).order_by(DatasetColumn.column_index))
        numeric = [column.column_name for column in columns.scalars().all() if column.semantic_type == "numeric"]
        if numeric:
            return [
                QueryPlan(
                    step_index=1,
                    purpose=f"Average {numeric[0]}",
                    sql=f'SELECT AVG("{numeric[0]}") AS average_{numeric[0]} FROM user_data."{dataset.physical_table_name}"',
                )
            ]
        return [self.sql_generation.row_count_plan(dataset.physical_table_name)]

    async def _answer(
        self,
        session: AsyncSession,
        dataset: Dataset,
        question: str,
        intent: str,
        results: list[QueryResultSummary],
        settings: Settings,
    ) -> tuple[str, list[dict]]:
        if intent == "schema_question":
            columns = await session.execute(select(DatasetColumn).where(DatasetColumn.dataset_id == dataset.id).order_by(DatasetColumn.column_index))
            column_rows = [
                {"column": column.column_name, "type": column.semantic_type, "postgres_type": column.postgres_type}
                for column in columns.scalars().all()
            ]
            content = f"{dataset.name} has {len(column_rows)} columns."
            blocks = self.block_service.build_blocks(content=content, rows=column_rows, columns=["column", "type", "postgres_type"])
        elif intent == "quality_question":
            issues = await session.execute(select(DatasetQualityIssue).where(DatasetQualityIssue.dataset_id == dataset.id))
            issue_rows = [{"issue": issue.title, "severity": issue.severity} for issue in issues.scalars().all()]
            content = "I reviewed dataset quality issues."
            blocks = self.block_service.build_blocks(
                content=content,
                rows=issue_rows,
                columns=["issue", "severity"],
                quality_note={"severity": dataset.quality_status if dataset.quality_status in {"info", "warning", "critical"} else "info", "title": "Quality status", "description": dataset.quality_status or "good"},
            )
        else:
            first = results[0] if results else None
            rows = first.rows if first else []
            columns = first.columns if first else []
            content = "I analyzed the dataset and prepared the result."
            if rows and "row_count" in rows[0]:
                content = f"This dataset contains {rows[0]['row_count']} rows."
            blocks = self.block_service.build_blocks(
                content=content,
                rows=rows,
                columns=columns,
                kpis=[{"label": "Rows", "value": dataset.row_count, "caption": "After duplicate removal"}],
            )
        return content, self.block_service.filter_for_environment(blocks, settings.app_env)

    async def _persist_assistant(
        self,
        session: AsyncSession,
        analysis_run: AnalysisRun,
        content: str,
        blocks: list[dict],
    ) -> ChatMessage:
        existing = await session.execute(
            select(ChatMessage).where(ChatMessage.chat_session_id == analysis_run.chat_session_id, ChatMessage.role == "assistant", ChatMessage.id == analysis_run.assistant_message_id)
        )
        message = existing.scalar_one_or_none()
        if message:
            return message

        next_index_result = await session.execute(
            select(func.coalesce(func.max(ChatMessage.message_index), 0)).where(ChatMessage.chat_session_id == analysis_run.chat_session_id)
        )
        message = ChatMessage(
            chat_session_id=analysis_run.chat_session_id,
            message_index=int(next_index_result.scalar_one()) + 1,
            role="assistant",
            content=content,
            blocks=blocks,
        )
        session.add(message)
        await session.flush()
        return message

    async def _checkpoint(self, session: AsyncSession, analysis_run: AnalysisRun) -> None:
        await session.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS analysis_checkpoints (
                    thread_id TEXT NOT NULL,
                    checkpoint_ns TEXT NOT NULL,
                    payload JSONB NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    PRIMARY KEY (thread_id, checkpoint_ns)
                )
                """
            )
        )
        await session.execute(
            text(
                """
                INSERT INTO analysis_checkpoints (thread_id, checkpoint_ns, payload)
                VALUES (:thread_id, :checkpoint_ns, CAST(:payload AS JSONB))
                ON CONFLICT (thread_id, checkpoint_ns) DO UPDATE SET payload = EXCLUDED.payload
                """
            ),
            {
                "thread_id": str(analysis_run.chat_session_id),
                "checkpoint_ns": str(analysis_run.id),
                "payload": '{"status": "completed"}',
            },
        )
