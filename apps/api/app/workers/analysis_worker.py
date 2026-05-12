from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select

from app.core.config import Settings, get_settings
from app.core.database import SessionLocal
from app.db.models import AnalysisRun
from app.services.analyst_workflow_service import AnalystWorkflowService


class AnalysisWorker:
    def __init__(self, settings: Settings | None = None, workflow: AnalystWorkflowService | None = None) -> None:
        self.settings = settings or get_settings()
        self.workflow = workflow or AnalystWorkflowService()

    async def run_once(self) -> int:
        processed = 0
        async with SessionLocal() as session:
            result = await session.execute(select(AnalysisRun).where(AnalysisRun.status == "queued").order_by(AnalysisRun.created_at))
            runs = list(result.scalars().all())
            for run in runs:
                run_id = run.id
                try:
                    await self.workflow.run_analysis(session, run, self.settings)
                except Exception:
                    await session.rollback()
                    failed = await session.get(AnalysisRun, run_id)
                    if failed:
                        failed.status = "failed"
                        failed.current_stage = "failed"
                        failed.error_code = "ANALYSIS_WORKFLOW_FAILED"
                        failed.error_message = (
                            "Sherlock could not complete this analysis. Try rephrasing the question "
                            "or asking a narrower question."
                        )
                        failed.completed_at = datetime.now(UTC)
                        await session.commit()
                processed += 1
        return processed
