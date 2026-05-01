import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import Settings, get_settings
from app.core.database import get_db_session
from app.core.errors import ApiError
from app.db.models import AnalysisRun, QueryAttempt
from app.db.models import AppUser


router = APIRouter(prefix="/internal", tags=["Internal"])


@router.get("/analysis-runs/{analysis_run_id}/query-attempts")
async def read_internal_query_attempts(
    analysis_run_id: uuid.UUID,
    user: AppUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> dict[str, object]:
    _guard_internal(settings)
    result = await session.execute(select(QueryAttempt).where(QueryAttempt.analysis_run_id == analysis_run_id).order_by(QueryAttempt.step_index, QueryAttempt.attempt_number))
    return {
        "data": [
            {
                "id": attempt.id,
                "analysis_run_id": attempt.analysis_run_id,
                "step_index": attempt.step_index,
                "attempt_number": attempt.attempt_number,
                "validation_status": attempt.validation_status,
                "execution_status": attempt.execution_status,
                "error_message": attempt.error_message,
                "result_preview": attempt.result_preview,
            }
            for attempt in result.scalars().all()
        ]
    }


@router.get("/analysis-runs/{analysis_run_id}/trace")
async def read_internal_trace(
    analysis_run_id: uuid.UUID,
    user: AppUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> dict[str, object]:
    _guard_internal(settings)
    run = await session.get(AnalysisRun, analysis_run_id)
    if not run:
        raise ApiError(status_code=status.HTTP_404_NOT_FOUND, code="NOT_FOUND", message="Analysis run not found.")
    return {"data": run.graph_trace or {}}


def _guard_internal(settings: Settings) -> None:
    if settings.app_env == "production":
        raise ApiError(status_code=status.HTTP_403_FORBIDDEN, code="FORBIDDEN", message="Internal endpoint is not available.")
