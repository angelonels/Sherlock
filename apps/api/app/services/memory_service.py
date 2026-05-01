from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ChatMessage, ChatSession


class MemoryService:
    message_threshold = 16
    token_threshold = 12_000

    async def maybe_compress_memory(self, session: AsyncSession, chat: ChatSession) -> None:
        count_result = await session.execute(
            select(func.count(ChatMessage.id)).where(
                ChatMessage.chat_session_id == chat.id,
                ChatMessage.deleted_at.is_(None),
                ChatMessage.role.in_(["user", "assistant"]),
            )
        )
        message_count = int(count_result.scalar_one())
        token_estimate = await self._estimate_tokens(session, chat)
        if message_count <= self.message_threshold and token_estimate <= self.token_threshold:
            return

        result = await session.execute(
            select(ChatMessage)
            .where(ChatMessage.chat_session_id == chat.id, ChatMessage.deleted_at.is_(None))
            .order_by(ChatMessage.message_index.desc())
            .limit(8)
        )
        last_messages = list(reversed(result.scalars().all()))
        summary_lines = []
        if chat.memory_summary:
            summary_lines.append(chat.memory_summary)
        for message in last_messages:
            content = (message.content or "").strip()
            if content:
                summary_lines.append(f"{message.role}: {content[:500]}")
        chat.memory_summary = "\n".join(summary_lines)[-4000:]
        chat.memory_summary_version += 1
        chat.last_summarized_message_id = last_messages[-1].id if last_messages else chat.last_summarized_message_id
        chat.memory_token_estimate = min(token_estimate, 12_000)
        await session.flush()

    async def _estimate_tokens(self, session: AsyncSession, chat: ChatSession) -> int:
        result = await session.execute(
            select(ChatMessage.content).where(ChatMessage.chat_session_id == chat.id, ChatMessage.deleted_at.is_(None))
        )
        chars = sum(len(content or "") for content in result.scalars().all())
        return chars // 4
