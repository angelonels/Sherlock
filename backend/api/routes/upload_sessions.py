from datetime import datetime, timedelta, timezone
from pathlib import Path
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import current_user
from database import get_db
from models.dataset import UploadSession
from models.user import User
from schemas.common import ResourceEnvelope
from schemas.dataset import UploadSessionResponse


router = APIRouter(prefix="/upload-sessions", tags=["Upload Sessions"])

MAX_UPLOAD_BYTES = 25 * 1024 * 1024
ALLOWED_EXTENSIONS = {"csv", "xlsx"}


@router.post("", response_model=ResourceEnvelope[UploadSessionResponse], status_code=status.HTTP_201_CREATED)
async def create_upload_session(
    file: UploadFile = File(...),
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    filename = file.filename or "upload"
    extension = Path(filename).suffix.lower().lstrip(".")
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Only CSV and XLSX files are supported.")

    contents = await file.read()
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File exceeds the 25 MB upload limit.")
    if not contents:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

    temp_dir = Path("tmp/uploads")
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_file_key = f"{uuid.uuid4()}.{extension}"
    (temp_dir / temp_file_key).write_bytes(contents)

    upload_session = UploadSession(
        user_id=user.id,
        original_filename=filename,
        file_extension=extension,
        temp_file_key=temp_file_key,
        file_size_bytes=len(contents),
        status="uploaded",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
        warnings=[],
    )
    db.add(upload_session)
    await db.commit()
    await db.refresh(upload_session)

    return {"data": upload_session, "links": {"self": f"/api/v1/upload-sessions/{upload_session.id}"}}
