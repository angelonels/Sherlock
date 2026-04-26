from __future__ import annotations

from sqlalchemy import select

from app.core.config import Settings, get_settings
from app.core.database import SessionLocal
from app.db.models import Dataset
from app.services.ingestion_service import IngestionService


class DatasetWorker:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.ingestion_service = IngestionService()

    async def run_once(self) -> int:
        processed = 0
        async with SessionLocal() as session:
            result = await session.execute(
                select(Dataset).where(Dataset.status == "processing", Dataset.deleted_at.is_(None)).order_by(Dataset.created_at)
            )
            datasets = list(result.scalars().all())
            for dataset in datasets:
                await self.ingestion_service.ingest_dataset(session, dataset, self.settings)
                processed += 1
        return processed
