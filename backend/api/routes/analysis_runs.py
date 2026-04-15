from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import current_user
from database import get_db
from models.analysis import AnalysisRun
from models.chat import ChatSession
from models.user import User
from schemas.analysis import AnalysisRunResponse
from schemas.common import ResourceEnvelope


router = APIRouter(prefix="/analysis-runs", tags=["Analysis Runs"])


@router.get("/{analysis_run_id}", response_model=ResourceEnvelope[AnalysisRunResponse])
async def get_analysis_run(
    analysis_run_id: str,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AnalysisRun)
        .join(ChatSession, AnalysisRun.chat_session_id == ChatSession.id)
        .where(AnalysisRun.id == analysis_run_id, ChatSession.user_id == user.id)
    )
    run = result.scalar_one_or_none()
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis run not found.")
    return {"data": run}
