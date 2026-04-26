import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import UploadSession
from app.db.repositories.base import Repository


class UploadSessionsRepository(Repository[UploadSession]):
    model = UploadSession

    async def get_for_user(
        self,
        session: AsyncSession,
        upload_session_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> UploadSession | None:
        result = await session.execute(
            select(UploadSession).where(
                UploadSession.id == upload_session_id,
                UploadSession.user_id == user_id,
                UploadSession.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()
