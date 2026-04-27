from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ChatSession
from app.db.repositories.base import Repository


class ChatsRepository(Repository[ChatSession]):
    model = ChatSession

    async def list_for_user(self, session: AsyncSession, user_id: object) -> list[ChatSession]:
        result = await session.execute(
            select(ChatSession)
            .where(ChatSession.user_id == user_id, ChatSession.deleted_at.is_(None))
            .order_by(ChatSession.updated_at.desc())
        )
        return list(result.scalars().all())

