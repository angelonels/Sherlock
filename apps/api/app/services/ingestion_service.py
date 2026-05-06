from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from io import BytesIO, StringIO
from typing import Any

import pandas as pd
from fastapi import status
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.errors import ApiError
from app.db.models import Dataset, DatasetColumn, DatasetQualityIssue, UploadSession
from app.services.column_cleaner import clean_column_names
from app.services.csv_utils import detect_delimiter, detect_encoding
from app.services.dataframe_profiler import profile_columns
from app.services.duplicate_service import drop_exact_duplicates
from app.services.missing_value_service import normalize_missing_values
from app.services.quality_service import build_quality_issues, quality_status
from app.services.row_hash import row_hash
from app.services.type_mapper import postgres_type_for_series
from app.services.upload_safety import delete_temp_file, read_temp_file


logger = logging.getLogger("sherlock.ingestion")


def quote_ident(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def physical_table_name(dataset_id: uuid.UUID) -> str:
    return f"dataset_{dataset_id.hex}"


class IngestionService:
    async def ingest_dataset(self, session: AsyncSession, dataset: Dataset, settings: Settings) -> Dataset:
        dataset_id = dataset.id
        user_id = dataset.user_id
        try:
            upload_session = await session.get(UploadSession, dataset.upload_session_id)
            if not upload_session:
                raise ApiError(status_code=status.HTTP_404_NOT_FOUND, code="UPLOAD_SESSION_NOT_FOUND", message="Upload session not found.")

            raw = read_temp_file(settings, upload_session.temp_file_key)
            frame = self._read_upload(upload_session, raw)
            original_row_count = len(frame)
            original_names = self._clean_frame_columns(frame)
            frame = normalize_missing_values(frame)
            frame, duplicate_rows_removed = drop_exact_duplicates(frame)
            frame["_sherlock_row_hash"] = frame.apply(row_hash, axis=1)

            table_name = physical_table_name(dataset.id)
            dataset.physical_table_name = table_name
            await self._create_physical_table(session, table_name, frame)
            await self._insert_rows(session, table_name, frame)

            profiles = profile_columns(frame.drop(columns=["_sherlock_row_hash"]), original_names)
            issues = build_quality_issues(
                frame,
                duplicate_rows_removed=duplicate_rows_removed,
                column_profiles=profiles,
            )
            for profile in profiles:
                session.add(DatasetColumn(dataset_id=dataset.id, **profile))
            for issue in issues:
                session.add(DatasetQualityIssue(dataset_id=dataset.id, **issue))

            status_name, score = quality_status(issues)
            dataset.status = "ready"
            dataset.original_row_count = original_row_count
            dataset.row_count = len(frame)
            dataset.duplicate_rows_removed = duplicate_rows_removed
            dataset.column_count = len(profiles)
            dataset.total_missing_values = int(frame.drop(columns=["_sherlock_row_hash"]).isna().sum().sum())
            dataset.quality_status = status_name
            dataset.quality_score = score
            upload_session.status = "ingested"
            await session.commit()

            try:
                delete_temp_file(settings, upload_session.temp_file_key)
            except OSError:
                logger.exception(
                    "raw upload cleanup deferred",
                    extra={
                        "job_name": "ingest_dataset",
                        "user_id": str(user_id),
                        "dataset_id": str(dataset_id),
                        "status": "ready",
                        "error_code": "RAW_UPLOAD_CLEANUP_DEFERRED",
                    },
                )
            else:
                dataset.raw_file_deleted_at = datetime.now(UTC)
                await session.commit()

            await session.refresh(dataset)
            return dataset
        except (OperationalError, ConnectionError, TimeoutError):
            await session.rollback()
            raise
        except Exception:
            logger.exception(
                "dataset ingestion failed",
                extra={
                    "job_name": "ingest_dataset",
                    "user_id": str(user_id),
                    "dataset_id": str(dataset_id),
                    "status": "failed",
                    "error_code": "DATASET_INGESTION_FAILED",
                },
            )
            await session.rollback()
            failed_dataset = await session.get(Dataset, dataset_id)
            if not failed_dataset:
                raise RuntimeError("Dataset disappeared while recording ingestion failure")
            failed_dataset.status = "failed"
            failed_dataset.ingestion_error = (
                "Sherlock could not ingest this file. Check the file structure and try a new upload."
            )
            await session.commit()
            await session.refresh(failed_dataset)
            return failed_dataset

    def _read_upload(self, upload_session: UploadSession, raw: bytes) -> pd.DataFrame:
        if upload_session.file_extension == "csv":
            encoding = detect_encoding(raw)
            text_payload = raw.decode(encoding)
            delimiter = detect_delimiter(text_payload)
            return pd.read_csv(StringIO(text_payload), delimiter=delimiter)

        return pd.read_excel(BytesIO(raw), sheet_name=upload_session.selected_sheet_name or (upload_session.sheet_names or [None])[0])

    def _clean_frame_columns(self, frame: pd.DataFrame) -> dict[str, str]:
        original_headers = [str(column) for column in frame.columns]
        clean_headers = clean_column_names(original_headers)
        frame.columns = clean_headers
        return {clean: original for clean, original in zip(clean_headers, original_headers, strict=True)}

    async def _create_physical_table(self, session: AsyncSession, table_name: str, frame: pd.DataFrame) -> None:
        await session.execute(text("CREATE SCHEMA IF NOT EXISTS user_data"))
        columns_sql = [
            "_sherlock_row_id BIGSERIAL PRIMARY KEY",
            "_sherlock_row_hash TEXT NOT NULL",
        ]
        for column_name in frame.columns:
            if column_name == "_sherlock_row_hash":
                continue
            columns_sql.append(f"{quote_ident(column_name)} {postgres_type_for_series(frame[column_name])}")
        await session.execute(text(f"DROP TABLE IF EXISTS user_data.{quote_ident(table_name)}"))
        await session.execute(text(f"CREATE TABLE user_data.{quote_ident(table_name)} ({', '.join(columns_sql)})"))

    async def _insert_rows(self, session: AsyncSession, table_name: str, frame: pd.DataFrame) -> None:
        user_columns = [column for column in frame.columns if column != "_sherlock_row_hash"]
        insert_columns = ["_sherlock_row_hash", *user_columns]
        sql = text(
            f"INSERT INTO user_data.{quote_ident(table_name)} "
            f"({', '.join(quote_ident(column) for column in insert_columns)}) "
            f"VALUES ({', '.join(':' + column for column in insert_columns)})"
        )
        rows: list[dict[str, Any]] = []
        for _, row in frame.iterrows():
            rows.append({column: self._db_value(row[column]) for column in insert_columns})
        if rows:
            await session.execute(sql, rows)

    def _db_value(self, value: Any) -> Any:
        if pd.isna(value):
            return None
        if hasattr(value, "to_pydatetime"):
            return value.to_pydatetime()
        if hasattr(value, "item"):
            return value.item()
        return value
