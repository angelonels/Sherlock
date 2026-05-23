from __future__ import annotations

import json
import time
from datetime import UTC, datetime

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.models import AnalysisPlan, DatasetColumnContext, DatasetContext, DatasetQualityIssueContext, QueryResultSummary
from app.agents.checkpointing import open_checkpointer
from app.agents.state import AnalystState
from app.agents.subgraphs.query_execution import QueryExecutionSubgraph
from app.core.config import Settings
from app.db.models import AnalysisRun, ChatMessage, ChatSession, Dataset, DatasetColumn, DatasetQualityIssue
from app.services.block_service import BlockService
from app.services.chart_service import ChartService
from app.services.llm_service import LlmService
from app.services.memory_service import MemoryService
from app.services.prompt_service import PromptService
from app.services.title_service import TitleService


class AnalystGraph:
    def __init__(
        self,
        *,
        llm_service: LlmService | None = None,
        prompt_service: PromptService | None = None,
        query_subgraph: QueryExecutionSubgraph | None = None,
        block_service: BlockService | None = None,
        chart_service: ChartService | None = None,
        memory_service: MemoryService | None = None,
        title_service: TitleService | None = None,
    ) -> None:
        self.llm_service = llm_service or LlmService()
        self.prompt_service = prompt_service or PromptService()
        self.query_subgraph = query_subgraph or QueryExecutionSubgraph()
        self.block_service = block_service or BlockService()
        self.chart_service = chart_service or ChartService()
        self.memory_service = memory_service or MemoryService()
        self.title_service = title_service or TitleService()
        builder = StateGraph(AnalystState)
        builder.add_node("load_context", self.load_context)
        builder.add_node("prepare_context", self.prepare_context)
        builder.add_node("plan_analysis", self.plan_analysis)
        builder.add_node("execute_queries", self.execute_queries)
        builder.add_node("synthesize_answer", self.synthesize_answer)
        builder.add_node("build_blocks", self.build_blocks)
        builder.add_node("persist_outputs", self.persist_outputs)
        builder.add_edge(START, "load_context")
        builder.add_edge("load_context", "prepare_context")
        builder.add_edge("prepare_context", "plan_analysis")
        builder.add_edge("plan_analysis", "execute_queries")
        builder.add_edge("execute_queries", "synthesize_answer")
        builder.add_edge("synthesize_answer", "build_blocks")
        builder.add_edge("build_blocks", "persist_outputs")
        builder.add_edge("persist_outputs", END)
        self.builder = builder

    async def run(
        self,
        *,
        session: AsyncSession,
        analysis_run: AnalysisRun,
        settings: Settings,
    ) -> AnalysisRun:
        started = time.perf_counter()
        if analysis_run.assistant_message_id:
            return analysis_run

        analysis_run.status = "running"
        analysis_run.current_stage = "loading_context"
        analysis_run.started_at = datetime.now(UTC)
        await session.flush()

        invocation_input = {
            "analysis_run_id": str(analysis_run.id),
            "chat_id": str(analysis_run.chat_session_id),
            "user_message_id": str(analysis_run.user_message_id),
            "user_question": "",
        }
        invocation_config = {
            "configurable": {
                "thread_id": str(analysis_run.chat_session_id),
                "checkpoint_ns": str(analysis_run.id),
            },
            "metadata": {
                "analysis_run_id": str(analysis_run.id),
                "user_message_id": str(analysis_run.user_message_id),
                "session": session,
                "analysis_run": analysis_run,
                "settings": settings,
                "started": started,
            },
        }

        async with open_checkpointer(settings) as checkpointer:
            compiled = self.builder.compile(checkpointer=checkpointer)
            state = await compiled.ainvoke(
                invocation_input,
                config=invocation_config,
                durability="async" if settings.app_env == "development" else "sync",
            )
        assistant = await session.get(ChatMessage, state["assistant_message_id"])
        if not assistant:
            raise RuntimeError("Analysis graph completed without a persisted assistant message")
        chat = await session.get(ChatSession, analysis_run.chat_session_id)
        if not chat:
            raise RuntimeError("Analysis graph completed without a chat session")
        analysis_run.assistant_message_id = assistant.id
        analysis_run.status = "partial_success" if state.get("query_failures") and state.get("query_results") else "success"
        analysis_run.current_stage = "completed"
        analysis_run.completed_at = datetime.now(UTC)
        analysis_run.total_duration_ms = int((time.perf_counter() - started) * 1000)
        analysis_run.graph_trace = {
            "query_results": [result.model_dump() for result in state.get("query_results", [])],
            "query_failures": [result.model_dump() for result in state.get("query_failures", [])],
        }
        analysis_run.checkpoint_thread_id = str(analysis_run.chat_session_id)
        analysis_run.checkpoint_run_id = str(analysis_run.id)
        await self.title_service.generate_after_success(session, chat, state["user_question"])
        await self.memory_service.maybe_compress_memory(session, chat)
        await self._checkpoint(session, analysis_run, state)
        await session.commit()
        await session.refresh(analysis_run)
        return analysis_run

    async def load_context(self, state: AnalystState, config: RunnableConfig) -> AnalystState:
        session, analysis_run, _settings = self._runtime(config)
        analysis_run.current_stage = "loading_context"
        user_message = await session.get(ChatMessage, analysis_run.user_message_id)
        chat = await session.get(ChatSession, analysis_run.chat_session_id)
        if not user_message or not chat:
            raise RuntimeError("Analysis run is missing its chat context")
        dataset = await session.get(Dataset, chat.dataset_id)
        if not dataset:
            raise RuntimeError("Analysis run chat is missing its dataset")
        columns_result = await session.execute(
            select(DatasetColumn).where(DatasetColumn.dataset_id == dataset.id).order_by(DatasetColumn.column_index)
        )
        issues_result = await session.execute(select(DatasetQualityIssue).where(DatasetQualityIssue.dataset_id == dataset.id))
        await session.flush()
        return {
            **state,
            "user_message_id": str(user_message.id),
            "dataset": self._dataset_context(dataset),
            "dataset_id": str(dataset.id),
            "user_question": (user_message.content or "").strip(),
            "memory_summary": (chat.memory_summary or "")[-4000:] or None,
            "columns": [self._column_context(column) for column in columns_result.scalars().all()],
            "quality_issues": [self._quality_issue_context(issue) for issue in issues_result.scalars().all()],
        }

    async def prepare_context(self, state: AnalystState, config: RunnableConfig) -> AnalystState:
        session, analysis_run, _settings = self._runtime(config)
        analysis_run.current_stage = "planning"
        await session.flush()
        return state

    async def plan_analysis(self, state: AnalystState, config: RunnableConfig) -> AnalystState:
        session, analysis_run, _settings = self._runtime(config)
        prompt = self.prompt_service.build_planner_prompt(
            dataset=state["dataset"],
            columns=state["columns"],
            quality_issues=state["quality_issues"],
            question=state["user_question"],
            memory_summary=state.get("memory_summary"),
        )
        payload = await self.llm_service.complete_json(prompt)
        plan = AnalysisPlan.model_validate(payload)
        query_plans = plan.query_plans[:5]
        analysis_run.intent = plan.intent
        analysis_run.planner_output = {"query_plans": [query_plan.model_dump() for query_plan in query_plans]}
        await session.flush()
        return {**state, "intent": plan.intent, "query_plans": query_plans}

    async def execute_queries(self, state: AnalystState, config: RunnableConfig) -> AnalystState:
        session, analysis_run, _settings = self._runtime(config)
        results: list[QueryResultSummary] = []
        failures: list[QueryResultSummary] = []
        plans = state.get("query_plans", [])
        if plans:
            analysis_run.current_stage = "querying"
            await session.flush()
        for plan in plans[:5]:
            result = await self.query_subgraph.run(
                session,
                dataset_id=state["dataset"].id,
                physical_table_name=state["dataset"].physical_table_name,
                analysis_run_id=analysis_run.id,
                plan=plan,
            )
            (results if result.status == "success" else failures).append(result)
        return {**state, "query_results": results, "query_failures": failures}

    async def synthesize_answer(self, state: AnalystState, config: RunnableConfig) -> AnalystState:
        session, analysis_run, _settings = self._runtime(config)
        analysis_run.current_stage = "synthesizing"
        await session.flush()
        intent = state.get("intent", "data_question")
        if intent in {"data_question", "summary_question"} and state.get("query_failures") and not state.get("query_results"):
            return {
                **state,
                "content": "I could not safely run the analysis query for this question. Try rephrasing the question or checking that the relevant columns exist in the dataset.",
            }
        if intent == "schema_question":
            content = f"{state['dataset'].name} has {len(state['columns'])} columns."
            return {**state, "content": content}
        if intent == "quality_question":
            return {**state, "content": "I reviewed dataset quality issues."}
        summaries = [
            {
                "purpose": result.purpose,
                "columns": result.columns,
                "rows": result.rows,
                "row_count": result.row_count,
            }
            for result in state.get("query_results", [])
        ]
        prompt = self.prompt_service.build_answer_prompt(
            dataset=state["dataset"],
            question=state["user_question"],
            query_summaries=summaries,
            quality_issues=state["quality_issues"],
            memory_summary=state.get("memory_summary"),
        )
        content = (await self.llm_service.complete(prompt)).strip()
        if not content:
            content = "I could not produce a reliable answer from the available evidence."
        return {**state, "content": content}

    async def build_blocks(self, state: AnalystState, config: RunnableConfig) -> AnalystState:
        session, analysis_run, settings = self._runtime(config)
        analysis_run.current_stage = "building_response"
        await session.flush()
        intent = state.get("intent", "data_question")
        if intent == "schema_question":
            rows = [
                {"column": column.column_name, "type": column.semantic_type, "postgres_type": column.postgres_type}
                for column in state["columns"]
            ]
            blocks = self.block_service.build_blocks(
                content=state["content"],
                rows=rows,
                columns=["column", "type", "postgres_type"],
            )
        elif intent == "quality_question":
            issue_rows = [{"issue": issue.title, "severity": issue.severity} for issue in state["quality_issues"]]
            blocks = self.block_service.build_blocks(
                content=state["content"],
                rows=issue_rows,
                columns=["issue", "severity"],
                quality_note={
                    "severity": state["dataset"].quality_status
                    if state["dataset"].quality_status in {"info", "warning", "critical"}
                    else "info",
                    "title": "Quality status",
                    "description": state["dataset"].quality_status or "good",
                },
            )
        else:
            if state.get("query_failures") and not state.get("query_results"):
                blocks = self.block_service.validate_blocks(
                    [
                        {"type": "markdown", "content": state["content"]},
                        {
                            "type": "error",
                            "title": "Analysis query was not safe to run",
                            "message": (
                                "Sherlock could not safely run this analysis. "
                                "Try rephrasing the question or asking about fewer columns."
                            ),
                        },
                    ]
                )
                return {**state, "blocks": self.block_service.filter_for_environment(blocks, settings.app_env)}
            first = state.get("query_results", [None])[0] if state.get("query_results") else None
            rows = first.rows if first else []
            columns = first.columns if first else []
            chart = self.chart_service.recommend(rows, title=first.purpose if first else "Result")
            blocks = self.block_service.build_blocks(
                content=state["content"],
                rows=rows,
                columns=columns,
                charts=[self.chart_service.chart_block(chart)] if chart else None,
                kpis=[{"label": "Rows", "value": state["dataset"].row_count, "caption": "After duplicate removal"}],
            )
        return {**state, "blocks": self.block_service.filter_for_environment(blocks, settings.app_env)}

    async def persist_outputs(self, state: AnalystState, config: RunnableConfig) -> AnalystState:
        session, analysis_run, _settings = self._runtime(config)
        existing = await session.execute(
            select(ChatMessage).where(
                ChatMessage.chat_session_id == analysis_run.chat_session_id,
                ChatMessage.role == "assistant",
                ChatMessage.id == analysis_run.assistant_message_id,
            )
        )
        message = existing.scalar_one_or_none()
        if not message:
            next_index_result = await session.execute(
                select(func.coalesce(func.max(ChatMessage.message_index), 0)).where(
                    ChatMessage.chat_session_id == analysis_run.chat_session_id
                )
            )
            message = ChatMessage(
                chat_session_id=analysis_run.chat_session_id,
                message_index=int(next_index_result.scalar_one()) + 1,
                role="assistant",
                content=state["content"],
                blocks=state["blocks"],
            )
            session.add(message)
            await session.flush()
        return {**state, "assistant_message_id": str(message.id)}

    def _runtime(self, config: RunnableConfig) -> tuple[AsyncSession, AnalysisRun, Settings]:
        metadata = config["metadata"]
        return metadata["session"], metadata["analysis_run"], metadata["settings"]

    def _dataset_context(self, dataset: Dataset) -> DatasetContext:
        return DatasetContext(
            id=str(dataset.id),
            name=dataset.name,
            physical_schema_name=dataset.physical_schema_name,
            physical_table_name=dataset.physical_table_name,
            row_count=dataset.row_count,
            column_count=dataset.column_count,
            quality_status=dataset.quality_status,
        )

    def _column_context(self, column: DatasetColumn) -> DatasetColumnContext:
        return DatasetColumnContext(
            column_name=column.column_name,
            original_column_name=column.original_column_name,
            column_index=column.column_index,
            postgres_type=column.postgres_type,
            pandas_type=column.pandas_type,
            semantic_type=column.semantic_type,
            nullable_count=column.nullable_count,
            nullable_ratio=column.nullable_ratio,
            distinct_count=column.distinct_count,
            sample_values=column.sample_values,
            min_value=column.min_value,
            max_value=column.max_value,
            warning_flags=column.warning_flags,
        )

    def _quality_issue_context(self, issue: DatasetQualityIssue) -> DatasetQualityIssueContext:
        return DatasetQualityIssueContext(
            issue_type=issue.issue_type,
            severity=issue.severity,
            title=issue.title,
            description=issue.description,
            affected_row_count=issue.affected_row_count,
            affected_ratio=issue.affected_ratio,
            sample_values=issue.sample_values,
        )

    async def _checkpoint(self, session: AsyncSession, analysis_run: AnalysisRun, state: AnalystState) -> None:
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
                "payload": json.dumps(
                    {
                        "status": "completed",
                        "intent": state.get("intent", "unknown"),
                        "query_count": len(state.get("query_results", [])),
                    }
                ),
            },
        )
