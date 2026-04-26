import uuid

from fastapi import APIRouter, Depends, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import Settings, get_settings
from app.core.database import get_db_session
from app.db.models import AppUser
from app.schemas.common import DataEnvelope
from app.schemas.upload_session import UploadSessionRead, UploadSessionUpdate
from app.services.upload_session_service import UploadSessionService


router = APIRouter(prefix="/upload-sessions", tags=["Upload Sessions"])
service = UploadSessionService()


@router.post("", response_model=DataEnvelope[UploadSessionRead], status_code=status.HTTP_201_CREATED)
async def create_upload_session(
    file: UploadFile,
    user: AppUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> DataEnvelope[UploadSessionRead]:
    upload_session = await service.create(session, user=user, file=file, settings=settings)
    return DataEnvelope(data=UploadSessionRead.model_validate(upload_session))


@router.get("/{upload_session_id}", response_model=DataEnvelope[UploadSessionRead])
async def read_upload_session(
    upload_session_id: uuid.UUID,
    user: AppUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> DataEnvelope[UploadSessionRead]:
    upload_session = await service.get_for_user(session, upload_session_id=upload_session_id, user=user)
    return DataEnvelope(data=UploadSessionRead.model_validate(upload_session))


@router.patch("/{upload_session_id}", response_model=DataEnvelope[UploadSessionRead])
async def update_upload_session(
    upload_session_id: uuid.UUID,
    payload: UploadSessionUpdate,
    user: AppUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> DataEnvelope[UploadSessionRead]:
    upload_session = await service.update_sheet(
        session,
        upload_session_id=upload_session_id,
        selected_sheet_name=payload.selected_sheet_name,
        user=user,
        settings=settings,
    )
    return DataEnvelope(data=UploadSessionRead.model_validate(upload_session))


@router.delete("/{upload_session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_upload_session(
    upload_session_id: uuid.UUID,
    user: AppUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> None:
    await service.delete(session, upload_session_id=upload_session_id, user=user, settings=settings)
