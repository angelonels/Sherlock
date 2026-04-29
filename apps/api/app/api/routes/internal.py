import uuid

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.api.routes._helpers import not_implemented
from app.db.models import AppUser


router = APIRouter(prefix="/internal", tags=["Internal"])


@router.get("/analysis-runs/{analysis_run_id}/query-attempts")
async def read_internal_query_attempts(
    analysis_run_id: uuid.UUID,
    user: AppUser = Depends(get_current_user),
) -> None:
    not_implemented("Internal query attempts")


@router.get("/analysis-runs/{analysis_run_id}/trace")
async def read_internal_trace(
    analysis_run_id: uuid.UUID,
    user: AppUser = Depends(get_current_user),
) -> None:
    not_implemented("Internal traces")

