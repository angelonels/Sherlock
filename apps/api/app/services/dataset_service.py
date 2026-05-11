from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

from fastapi import status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.errors import ApiError
from app.db.models import AppUser, Dataset, DatasetColumn, DatasetQualityIssue, UploadSession
from app.schemas.dataset import DatasetCreate
from app.services.ingestion_service import quote_ident
from app.services.job_dispatcher import JobDispatcher


logger = logging.getLogger("sherlock.datasets")


class DatasetService:
    def __init__(self, dispatcher: JobDispatcher | None = None) -> None:
        self.dispatcher = dispatcher or JobDispatcher()

    async def create_dataset(
        self,
        session: AsyncSession,
        *,
        payload: DatasetCreate,
        user: AppUser,
        settings: Settings,
    ) -> Dataset:
        upload_session = await session.get(UploadSession, payload.upload_session_id)
        if (
            not upload_session
            or upload_session.user_id != user.id
            or upload_session.deleted_at is not None
            or upload_session.status != "inspected"
        ):
            raise ApiError(status_code=status.HTTP_404_NOT_FOUND, code="NOT_FOUND", message="Upload session not found.")
        if upload_session.expires_at <= datetime.now(UTC):
            raise ApiError(status_code=status.HTTP_410_GONE, code="UPLOAD_SESSION_EXPIRED", message="Upload session has expired.")

        selected_sheet = payload.selected_sheet_name or upload_session.selected_sheet_name
        if upload_session.file_extension == "xlsx" and upload_session.sheet_names and len(upload_session.sheet_names) > 1:
            selected_sheet = selected_sheet or upload_session.sheet_names[0]

        dataset = Dataset(
            user_id=user.id,
            upload_session_id=upload_session.id,
            name=payload.name,
            original_filename=upload_session.original_filename,
            source_file_type=upload_session.file_extension,
            selected_sheet_name=selected_sheet,
            physical_table_name=f"dataset_pending_{uuid.uuid4().hex}",
            status="processing",
        )
        if selected_sheet and upload_session.selected_sheet_name != selected_sheet:
            upload_session.selected_sheet_name = selected_sheet
        session.add(dataset)
        await session.commit()
        await session.refresh(dataset)

        try:
            self.dispatcher.enqueue_dataset_ingestion(dataset.id)
        except Exception:
            logger.exception(
                "dataset ingestion dispatch failed",
                extra={
                    "job_name": "ingest_dataset",
                    "user_id": str(user.id),
                    "dataset_id": str(dataset.id),
                    "status": "failed",
                    "error_code": "DATASET_DISPATCH_FAILED",
                },
            )
            dataset.status = "failed"
            dataset.ingestion_error = "Sherlock could not start ingestion. Try creating the dataset again."
            await session.commit()
            await session.refresh(dataset)
        return dataset

    async def get_dataset(self, session: AsyncSession, dataset_id: uuid.UUID, user: AppUser) -> Dataset:
        result = await session.execute(
            select(Dataset).where(Dataset.id == dataset_id, Dataset.user_id == user.id, Dataset.deleted_at.is_(None))
        )
        dataset = result.scalar_one_or_none()
        if not dataset:
            raise ApiError(status_code=status.HTTP_404_NOT_FOUND, code="NOT_FOUND", message="Dataset not found.")
        return dataset

    async def list_datasets(self, session: AsyncSession, user: AppUser) -> list[Dataset]:
        result = await session.execute(
            select(Dataset).where(Dataset.user_id == user.id, Dataset.deleted_at.is_(None)).order_by(Dataset.created_at.desc())
        )
        return list(result.scalars().all())

    async def delete_dataset(self, session: AsyncSession, dataset_id: uuid.UUID, user: AppUser) -> None:
        dataset = await self.get_dataset(session, dataset_id, user)
        dataset.status = "deleted"
        dataset.deleted_at = datetime.now(UTC)
        if dataset.physical_table_name:
            await session.execute(text(f"DROP TABLE IF EXISTS user_data.{quote_ident(dataset.physical_table_name)}"))
            dataset.physical_table_dropped_at = datetime.now(UTC)
        await session.commit()

    async def list_columns(self, session: AsyncSession, dataset: Dataset) -> list[DatasetColumn]:
        result = await session.execute(
            select(DatasetColumn).where(DatasetColumn.dataset_id == dataset.id).order_by(DatasetColumn.column_index)
        )
        return list(result.scalars().all())

    async def list_quality_issues(self, session: AsyncSession, dataset: Dataset) -> list[DatasetQualityIssue]:
        result = await session.execute(
            select(DatasetQualityIssue).where(DatasetQualityIssue.dataset_id == dataset.id).order_by(DatasetQualityIssue.severity.desc(), DatasetQualityIssue.created_at)
        )
        return list(result.scalars().all())

    async def preview(self, session: AsyncSession, dataset: Dataset, *, limit: int, cursor: int | None) -> tuple[list[dict[str, object]], str | None]:
        if dataset.status not in {"ready", "locked"}:
            raise ApiError(status_code=status.HTTP_409_CONFLICT, code="DATASET_NOT_READY", message="Dataset preview is available once ingestion is ready.")
        safe_limit = min(max(limit, 1), 100)
        where = "WHERE _sherlock_row_id > :cursor" if cursor else ""
        columns = await self.list_columns(session, dataset)
        selected_columns = ["_sherlock_row_id", *(column.column_name for column in columns)]
        result = await session.execute(
            text(
                f"SELECT {', '.join(quote_ident(column) for column in selected_columns)} "
                f"FROM user_data.{quote_ident(dataset.physical_table_name)} {where} "
                "ORDER BY _sherlock_row_id ASC LIMIT :limit"
            ),
            {"cursor": cursor or 0, "limit": safe_limit + 1},
        )
        rows = [dict(row._mapping) for row in result.fetchall()]
        next_cursor = None
        if len(rows) > safe_limit:
            next_cursor = str(rows[-2]["_sherlock_row_id"])
            rows = rows[:safe_limit]
        return rows, next_cursor
