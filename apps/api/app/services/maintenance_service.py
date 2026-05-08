from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.db.models import AnalysisRun, Dataset, UploadSession
from app.services.upload_safety import delete_temp_file


class MaintenanceService:
    async def cleanup_ingested_upload_files(self, session: AsyncSession, settings: Settings) -> int:
        result = await session.execute(
            select(Dataset, UploadSession)
            .join(UploadSession, UploadSession.id == Dataset.upload_session_id)
            .where(
                Dataset.status.in_(["ready", "locked"]),
                Dataset.raw_file_deleted_at.is_(None),
                Dataset.deleted_at.is_(None),
            )
        )
        count = 0
        for dataset, upload_session in result.all():
            delete_temp_file(settings, upload_session.temp_file_key)
            dataset.raw_file_deleted_at = datetime.now(UTC)
            count += 1
        await session.commit()
        return count

    async def cleanup_expired_upload_sessions(self, session: AsyncSession, settings: Settings) -> int:
        result = await session.execute(
            select(UploadSession).where(
                UploadSession.expires_at <= datetime.now(UTC),
                UploadSession.deleted_at.is_(None),
                UploadSession.status.in_(["uploaded", "inspected"]),
            )
        )
        count = 0
        for upload_session in result.scalars().all():
            upload_session.status = "expired"
            delete_temp_file(settings, upload_session.temp_file_key)
            count += 1
        await session.commit()
        return count

    async def fail_stuck_analysis_runs(self, session: AsyncSession, *, max_age_minutes: int = 30) -> int:
        cutoff = datetime.now(UTC) - timedelta(minutes=max_age_minutes)
        result = await session.execute(
            select(AnalysisRun).where(AnalysisRun.status == "running", AnalysisRun.started_at < cutoff)
        )
        count = 0
        for run in result.scalars().all():
            run.status = "failed"
            run.current_stage = "failed"
            run.error_code = "STUCK_RUN"
            run.error_message = "Analysis run exceeded the allowed processing window."
            count += 1
        await session.commit()
        return count
