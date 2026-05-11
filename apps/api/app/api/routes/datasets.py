import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import Settings, get_settings
from app.core.database import get_db_session
from app.db.models import AppUser
from app.schemas.common import DataEnvelope, ListEnvelope
from app.schemas.dataset import (
    DatasetColumnRead,
    DatasetCreate,
    DatasetQualityIssueRead,
    DatasetRead,
)
from app.services.dataset_service import DatasetService


router = APIRouter(prefix="/datasets", tags=["Datasets"])
dataset_service = DatasetService()


@router.post("", response_model=DataEnvelope[DatasetRead], status_code=status.HTTP_202_ACCEPTED)
async def create_dataset(
    payload: DatasetCreate,
    user: AppUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> DataEnvelope[DatasetRead]:
    dataset = await dataset_service.create_dataset(session, payload=payload, user=user, settings=settings)
    return DataEnvelope(data=DatasetRead.model_validate(dataset))


@router.get("", response_model=ListEnvelope[DatasetRead])
async def list_datasets(
    user: AppUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    datasets = await dataset_service.list_datasets(session, user)
    return {"data": [DatasetRead.model_validate(dataset) for dataset in datasets], "pagination": {"next_cursor": None}}


@router.get("/{dataset_id}", response_model=DataEnvelope[DatasetRead])
async def read_dataset(
    dataset_id: uuid.UUID,
    user: AppUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> DataEnvelope[DatasetRead]:
    dataset = await dataset_service.get_dataset(session, dataset_id, user)
    return DataEnvelope(data=DatasetRead.model_validate(dataset))


@router.get("/{dataset_id}/columns", response_model=ListEnvelope[DatasetColumnRead])
async def list_dataset_columns(
    dataset_id: uuid.UUID,
    user: AppUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    dataset = await dataset_service.get_dataset(session, dataset_id, user)
    columns = await dataset_service.list_columns(session, dataset)
    return {"data": [DatasetColumnRead.model_validate(column) for column in columns], "pagination": {"next_cursor": None}}


@router.get("/{dataset_id}/quality-issues", response_model=ListEnvelope[DatasetQualityIssueRead])
async def list_dataset_quality_issues(
    dataset_id: uuid.UUID,
    user: AppUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    dataset = await dataset_service.get_dataset(session, dataset_id, user)
    issues = await dataset_service.list_quality_issues(session, dataset)
    return {"data": [DatasetQualityIssueRead.model_validate(issue) for issue in issues], "pagination": {"next_cursor": None}}


@router.get("/{dataset_id}/preview", response_model=ListEnvelope[dict[str, object]])
async def read_dataset_preview(
    dataset_id: uuid.UUID,
    limit: int = 100,
    cursor: int | None = None,
    user: AppUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    dataset = await dataset_service.get_dataset(session, dataset_id, user)
    rows, next_cursor = await dataset_service.preview(session, dataset, limit=limit, cursor=cursor)
    return {"data": rows, "pagination": {"next_cursor": next_cursor}}


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dataset(
    dataset_id: uuid.UUID,
    user: AppUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> None:
    await dataset_service.delete_dataset(session, dataset_id, user)
