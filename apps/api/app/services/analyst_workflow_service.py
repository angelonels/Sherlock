from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.graph import AnalystGraph
from app.core.config import Settings
from app.db.models import AnalysisRun
from app.services.llm_service import LlmService


class AnalystWorkflowService:
    """Thin adapter for the LangGraph-backed analyst workflow."""

    def __init__(self, *, graph: AnalystGraph | None = None, llm_service: LlmService | None = None) -> None:
        self.graph = graph or AnalystGraph(llm_service=llm_service)

    async def run_analysis(self, session: AsyncSession, analysis_run: AnalysisRun, settings: Settings) -> AnalysisRun:
        return await self.graph.run(session=session, analysis_run=analysis_run, settings=settings)
