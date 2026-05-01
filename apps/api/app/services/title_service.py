from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ChatSession


class TitleService:
    def generate(self, first_question: str) -> str:
        words = [word.strip(" .,!?;:") for word in first_question.split() if word.strip(" .,!?;:")]
        if not words:
            return "New investigation"
        title = " ".join(words[:8])
        return title[:80]

    async def generate_after_success(self, session: AsyncSession, chat: ChatSession, first_question: str) -> None:
        if chat.title != "New investigation":
            return
        chat.title = self.generate(first_question)
        await session.flush()
