import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db_session
from app.db.models import AppUser
from app.schemas.analysis_run import AnalysisRunRead
from app.schemas.common import DataEnvelope
from app.schemas.message import MessageRead
from app.services.analysis_run_service import AnalysisRunService


router = APIRouter(prefix="/analysis-runs", tags=["Analysis Runs"])
analysis_run_service = AnalysisRunService()


@router.get("/{analysis_run_id}", response_model=DataEnvelope[AnalysisRunRead])
async def read_analysis_run(
    analysis_run_id: uuid.UUID,
    user: AppUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> DataEnvelope[AnalysisRunRead]:
    run, assistant_message = await analysis_run_service.get_run(session, analysis_run_id, user)
    data = AnalysisRunRead.model_validate(run)
    data.assistant_message = MessageRead.model_validate(assistant_message) if assistant_message else None
    return DataEnvelope(data=data)
