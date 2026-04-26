from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Dataset
from app.db.repositories.base import Repository


class DatasetsRepository(Repository[Dataset]):
    model = Dataset

    async def list_for_user(self, session: AsyncSession, user_id: object) -> list[Dataset]:
        result = await session.execute(
            select(Dataset)
            .where(Dataset.user_id == user_id, Dataset.deleted_at.is_(None))
            .order_by(Dataset.created_at.desc())
        )
        return list(result.scalars().all())

