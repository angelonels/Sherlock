import hashlib

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import current_user
from database import get_db
from models.analysis import AnalysisRun, ChatMessage
from models.chat import ChatSession
from models.user import User
from schemas.analysis import MessageCreate, MessageResponse
from schemas.common import ListEnvelope


router = APIRouter(prefix="/chats/{chat_id}/messages", tags=["Messages"])


@router.get("", response_model=ListEnvelope[MessageResponse])
async def list_messages(chat_id: str, user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    chat = await _get_owned_chat(db, chat_id, user.id)
    result = await db.execute(
        select(ChatMessage).where(ChatMessage.chat_session_id == chat.id).order_by(ChatMessage.message_index.asc())
    )
    return {"data": result.scalars().all(), "pagination": {"next_cursor": None}}


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def create_message(
    chat_id: str,
    payload: MessageCreate,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    if not idempotency_key:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Idempotency-Key header is required.")

    chat = await _get_owned_chat(db, chat_id, user.id)
    body_hash = hashlib.sha256(payload.model_dump_json().encode("utf-8")).hexdigest()
    existing_result = await db.execute(
        select(ChatMessage).where(ChatMessage.chat_session_id == chat.id, ChatMessage.client_message_id == idempotency_key)
    )
    existing = existing_result.scalar_one_or_none()
    if existing:
        if existing.idempotency_body_hash != body_hash:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Idempotency-Key was reused with a different request body.")
        run_result = await db.execute(select(AnalysisRun).where(AnalysisRun.user_message_id == existing.id))
        return {"data": {"message": existing, "analysis_run": run_result.scalar_one()}}

    max_index_result = await db.execute(select(func.coalesce(func.max(ChatMessage.message_index), 0)).where(ChatMessage.chat_session_id == chat.id))
    next_index = int(max_index_result.scalar_one()) + 1
    message = ChatMessage(
        chat_session_id=chat.id,
        message_index=next_index,
        client_message_id=idempotency_key,
        idempotency_body_hash=body_hash,
        role="user",
        content=payload.content,
    )
    db.add(message)
    await db.flush()
    run = AnalysisRun(chat_session_id=chat.id, user_message_id=message.id, status="queued", current_stage="queued")
    db.add(run)
    await db.commit()
    await db.refresh(message)
    await db.refresh(run)
    return {"data": {"message": message, "analysis_run": run}, "links": {"analysis_run": f"/api/v1/analysis-runs/{run.id}"}}


async def _get_owned_chat(db: AsyncSession, chat_id: str, user_id: str) -> ChatSession:
    result = await db.execute(select(ChatSession).where(ChatSession.id == chat_id, ChatSession.user_id == user_id))
    chat = result.scalar_one_or_none()
    if chat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found.")
    return chat
