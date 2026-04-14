import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import current_user
from database import get_db
from models.dataset import Dataset, UploadSession
from models.user import User
from schemas.common import ResourceEnvelope
from schemas.dataset import DatasetCreate, DatasetResponse


router = APIRouter(prefix="/datasets", tags=["Datasets"])


@router.post("", response_model=ResourceEnvelope[DatasetResponse], status_code=status.HTTP_202_ACCEPTED)
async def create_dataset(
    payload: DatasetCreate,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UploadSession).where(UploadSession.id == payload.upload_session_id, UploadSession.user_id == user.id)
    )
    upload_session = result.scalar_one_or_none()
    if upload_session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload session not found.")
    if upload_session.status not in {"uploaded", "inspected"}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Upload session cannot be converted into a dataset.")

    dataset = Dataset(
        user_id=user.id,
        upload_session_id=upload_session.id,
        name=payload.name,
        original_filename=upload_session.original_filename,
        source_file_type=upload_session.file_extension,
        selected_sheet_name=payload.selected_sheet_name or upload_session.selected_sheet_name,
        physical_table_name=f"dataset_{uuid.uuid4().hex}",
        status="processing",
    )
    db.add(dataset)
    upload_session.status = "ingested"
    await db.commit()
    await db.refresh(dataset)
    return {"data": dataset, "links": {"self": f"/api/v1/datasets/{dataset.id}"}}


@router.get("/{dataset_id}", response_model=ResourceEnvelope[DatasetResponse])
async def get_dataset(dataset_id: str, user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id, Dataset.user_id == user.id))
    dataset = result.scalar_one_or_none()
    if dataset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found.")
    return {"data": dataset}
