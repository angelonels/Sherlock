from __future__ import annotations

from sqlalchemy import select

from app.core.config import Settings, get_settings
from app.core.database import SessionLocal
from app.db.models import AnalysisRun
from app.services.analyst_workflow_service import AnalystWorkflowService


class AnalysisWorker:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.workflow = AnalystWorkflowService()

    async def run_once(self) -> int:
        processed = 0
        async with SessionLocal() as session:
            result = await session.execute(select(AnalysisRun).where(AnalysisRun.status == "queued").order_by(AnalysisRun.created_at))
            runs = list(result.scalars().all())
            for run in runs:
                await self.workflow.run_analysis(session, run, self.settings)
                processed += 1
        return processed
