from __future__ import annotations

import uuid

from fastapi import status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.db.models import AnalysisRun, AppUser, ChatMessage, ChatSession


class AnalysisRunService:
    async def get_run(self, session: AsyncSession, analysis_run_id: uuid.UUID, user: AppUser) -> tuple[AnalysisRun, ChatMessage | None]:
        result = await session.execute(
            select(AnalysisRun, ChatMessage)
            .join(ChatSession, ChatSession.id == AnalysisRun.chat_session_id)
            .outerjoin(ChatMessage, ChatMessage.id == AnalysisRun.assistant_message_id)
            .where(AnalysisRun.id == analysis_run_id, ChatSession.user_id == user.id, ChatSession.deleted_at.is_(None))
        )
        row = result.first()
        if not row:
            raise ApiError(status_code=status.HTTP_404_NOT_FOUND, code="NOT_FOUND", message="Analysis run not found.")
        return row[0], row[1]
