from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from fastapi import UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.errors import ApiError
from app.db.models import AppUser, UploadSession
from app.db.repositories.upload_sessions import UploadSessionsRepository
from app.services.csv_utils import inspect_csv
from app.services.excel_utils import inspect_xlsx
from app.services.upload_safety import (
    build_temp_file_key,
    delete_temp_file,
    read_temp_file,
    validate_extension,
    validate_file_size,
    write_temp_file,
)


class UploadSessionService:
    def __init__(self) -> None:
        self.repository = UploadSessionsRepository()

    async def create(
        self,
        session: AsyncSession,
        *,
        user: AppUser,
        file: UploadFile,
        settings: Settings,
    ) -> UploadSession:
        await self._ensure_user(session, user)
        filename = file.filename or "upload"
        extension = validate_extension(filename)
        content = await file.read()
        validate_file_size(len(content), settings)

        inspection = inspect_csv(content, settings) if extension == "csv" else inspect_xlsx(content, settings)
        temp_file_key = build_temp_file_key(user.id, extension)
        write_temp_file(settings, temp_file_key, content)

        upload_session = UploadSession(
            user_id=user.id,
            original_filename=filename,
            file_extension=extension,
            temp_file_key=temp_file_key,
            file_size_bytes=len(content),
            status="inspected",
            sheet_names=inspection["sheet_names"],
            selected_sheet_name=inspection["selected_sheet_name"],
            preview_rows=inspection["preview_rows"],
            detected_columns=inspection["detected_columns"],
            warnings=inspection["warnings"],
            expires_at=datetime.now(UTC) + timedelta(minutes=settings.upload_session_ttl_minutes),
        )
        session.add(upload_session)
        await session.commit()
        await session.refresh(upload_session)
        setattr(upload_session, "recommended_sheet_name", inspection["recommended_sheet_name"])
        return upload_session

    async def get_for_user(
        self,
        session: AsyncSession,
        *,
        upload_session_id: uuid.UUID,
        user: AppUser,
    ) -> UploadSession:
        if user.id is None:
            raise self._not_found()
        upload_session = await self.repository.get_for_user(session, upload_session_id, user.id)
        if not upload_session:
            raise self._not_found()
        self._ensure_not_expired(upload_session)
        setattr(upload_session, "recommended_sheet_name", upload_session.sheet_names[0] if upload_session.sheet_names else None)
        return upload_session

    async def update_sheet(
        self,
        session: AsyncSession,
        *,
        upload_session_id: uuid.UUID,
        selected_sheet_name: str | None,
        user: AppUser,
        settings: Settings,
    ) -> UploadSession:
        upload_session = await self.get_for_user(session, upload_session_id=upload_session_id, user=user)
        if upload_session.file_extension != "xlsx":
            raise ApiError(status_code=status.HTTP_400_BAD_REQUEST, code="NOT_XLSX_UPLOAD", message="Sheet selection is only available for XLSX uploads.")
        if not selected_sheet_name:
            raise ApiError(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, code="SHEET_REQUIRED", message="selected_sheet_name is required.")

        content = read_temp_file(settings, upload_session.temp_file_key)
        inspection = inspect_xlsx(content, settings, selected_sheet_name)
        upload_session.selected_sheet_name = selected_sheet_name
        upload_session.preview_rows = inspection["preview_rows"]
        upload_session.detected_columns = inspection["detected_columns"]
        upload_session.warnings = inspection["warnings"]
        upload_session.sheet_names = inspection["sheet_names"]
        await session.commit()
        await session.refresh(upload_session)
        setattr(upload_session, "recommended_sheet_name", inspection["recommended_sheet_name"])
        return upload_session

    async def delete(
        self,
        session: AsyncSession,
        *,
        upload_session_id: uuid.UUID,
        user: AppUser,
        settings: Settings,
    ) -> None:
        upload_session = await self.get_for_user(session, upload_session_id=upload_session_id, user=user)
        upload_session.status = "deleted"
        upload_session.deleted_at = datetime.now(UTC)
        delete_temp_file(settings, upload_session.temp_file_key)
        await session.commit()

    async def _ensure_user(self, session: AsyncSession, user: AppUser) -> None:
        if user.id:
            existing = await session.get(AppUser, user.id)
            if existing:
                return

        result = await session.execute(select(AppUser).where(AppUser.clerk_user_id == user.clerk_user_id))
        existing_by_clerk = result.scalar_one_or_none()
        if existing_by_clerk:
            user.id = existing_by_clerk.id
            return

        user.id = user.id or uuid.uuid4()
        session.add(
            AppUser(
                id=user.id,
                clerk_user_id=user.clerk_user_id,
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                image_url=user.image_url,
            )
        )
        await session.flush()

    def _ensure_not_expired(self, upload_session: UploadSession) -> None:
        if upload_session.expires_at <= datetime.now(UTC):
            raise ApiError(status_code=status.HTTP_410_GONE, code="UPLOAD_SESSION_EXPIRED", message="Upload session has expired.")

    def _not_found(self) -> ApiError:
        return ApiError(status_code=status.HTTP_404_NOT_FOUND, code="NOT_FOUND", message="Upload session not found.")
