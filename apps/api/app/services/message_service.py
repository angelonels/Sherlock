from __future__ import annotations

import hashlib
import json
import uuid

from fastapi import status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.db.models import AnalysisRun, AppUser, ChatMessage, ChatSession
from app.schemas.message import MessageCreate


class MessageService:
    async def list_messages(self, session: AsyncSession, chat_id: uuid.UUID, user: AppUser) -> list[ChatMessage]:
        await self._get_chat(session, chat_id, user)
        result = await session.execute(
            select(ChatMessage)
            .where(ChatMessage.chat_session_id == chat_id, ChatMessage.deleted_at.is_(None))
            .order_by(ChatMessage.message_index)
        )
        return list(result.scalars().all())

    async def create_message(
        self,
        session: AsyncSession,
        *,
        chat_id: uuid.UUID,
        payload: MessageCreate,
        idempotency_key: str | None,
        user: AppUser,
    ) -> tuple[ChatMessage, AnalysisRun]:
        if not idempotency_key:
            raise ApiError(status_code=status.HTTP_400_BAD_REQUEST, code="IDEMPOTENCY_KEY_REQUIRED", message="Idempotency-Key header is required.")
        await self._get_chat(session, chat_id, user)
        body_hash = self._hash_body(payload)

        existing = await session.execute(
            select(ChatMessage, AnalysisRun)
            .join(AnalysisRun, AnalysisRun.user_message_id == ChatMessage.id)
            .where(ChatMessage.chat_session_id == chat_id, ChatMessage.client_message_id == idempotency_key)
        )
        existing_pair = existing.first()
        if existing_pair:
            message, run = existing_pair
            if message.idempotency_body_hash != body_hash:
                raise ApiError(status_code=status.HTTP_409_CONFLICT, code="IDEMPOTENCY_CONFLICT", message="Idempotency-Key was already used with a different body.")
            return message, run

        max_index_result = await session.execute(
            select(func.coalesce(func.max(ChatMessage.message_index), 0)).where(ChatMessage.chat_session_id == chat_id)
        )
        next_index = int(max_index_result.scalar_one()) + 1
        message = ChatMessage(
            chat_session_id=chat_id,
            message_index=next_index,
            client_message_id=idempotency_key,
            idempotency_body_hash=body_hash,
            role="user",
            content=payload.content,
        )
        session.add(message)
        await session.flush()
        run = AnalysisRun(
            chat_session_id=chat_id,
            user_message_id=message.id,
            status="queued",
            current_stage="queued",
        )
        session.add(run)
        await session.commit()
        await session.refresh(message)
        await session.refresh(run)
        return message, run

    async def _get_chat(self, session: AsyncSession, chat_id: uuid.UUID, user: AppUser) -> ChatSession:
        result = await session.execute(
            select(ChatSession).where(ChatSession.id == chat_id, ChatSession.user_id == user.id, ChatSession.deleted_at.is_(None))
        )
        chat = result.scalar_one_or_none()
        if not chat:
            raise ApiError(status_code=status.HTTP_404_NOT_FOUND, code="NOT_FOUND", message="Chat not found.")
        return chat

    def _hash_body(self, payload: MessageCreate) -> str:
        return hashlib.sha256(json.dumps(payload.model_dump(), sort_keys=True).encode()).hexdigest()
