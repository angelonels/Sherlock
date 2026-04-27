from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.db.models import AppUser, ChatSession, Dataset
from app.schemas.chat import ChatCreate, ChatUpdate


class ChatService:
    async def list_chats(self, session: AsyncSession, user: AppUser) -> list[ChatSession]:
        result = await session.execute(
            select(ChatSession).where(ChatSession.user_id == user.id, ChatSession.deleted_at.is_(None)).order_by(ChatSession.updated_at.desc())
        )
        return list(result.scalars().all())

    async def create_chat(self, session: AsyncSession, payload: ChatCreate, user: AppUser) -> ChatSession:
        result = await session.execute(
            select(Dataset).where(Dataset.id == payload.dataset_id, Dataset.user_id == user.id, Dataset.deleted_at.is_(None)).with_for_update()
        )
        dataset = result.scalar_one_or_none()
        if not dataset:
            raise ApiError(status_code=status.HTTP_404_NOT_FOUND, code="NOT_FOUND", message="Dataset not found.")
        if dataset.status != "ready":
            raise ApiError(status_code=status.HTTP_409_CONFLICT, code="DATASET_NOT_READY", message="Only ready datasets can start an investigation.")

        dataset.status = "locked"
        dataset.locked_at = datetime.now(UTC)
        chat = ChatSession(user_id=user.id, dataset_id=dataset.id, title=dataset.name or "New investigation")
        session.add(chat)
        try:
            await session.commit()
        except IntegrityError as exc:
            await session.rollback()
            raise ApiError(status_code=status.HTTP_409_CONFLICT, code="ACTIVE_CHAT_EXISTS", message="Dataset already has an active chat.") from exc
        await session.refresh(chat)
        return chat

    async def get_chat(self, session: AsyncSession, chat_id: uuid.UUID, user: AppUser) -> ChatSession:
        result = await session.execute(
            select(ChatSession).where(ChatSession.id == chat_id, ChatSession.user_id == user.id, ChatSession.deleted_at.is_(None))
        )
        chat = result.scalar_one_or_none()
        if not chat:
            raise ApiError(status_code=status.HTTP_404_NOT_FOUND, code="NOT_FOUND", message="Chat not found.")
        return chat

    async def update_chat(self, session: AsyncSession, chat_id: uuid.UUID, payload: ChatUpdate, user: AppUser) -> ChatSession:
        chat = await self.get_chat(session, chat_id, user)
        chat.title = payload.title
        await session.commit()
        await session.refresh(chat)
        return chat

    async def delete_chat(self, session: AsyncSession, chat_id: uuid.UUID, user: AppUser) -> None:
        chat = await self.get_chat(session, chat_id, user)
        chat.deleted_at = datetime.now(UTC)
        await session.commit()
