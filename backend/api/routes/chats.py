from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import current_user
from database import get_db
from models.chat import ChatSession
from models.dataset import Dataset
from models.user import User
from schemas.chat import ChatSessionResponse
from schemas.common import ListEnvelope, ResourceEnvelope


router = APIRouter(prefix="/chats", tags=["Chats"])


class ChatCreate(BaseModel):
    dataset_id: str


@router.get("", response_model=ListEnvelope[ChatSessionResponse])
async def list_chats(user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ChatSession).where(ChatSession.user_id == user.id, ChatSession.deleted_at.is_(None)).order_by(ChatSession.updated_at.desc())
    )
    return {"data": result.scalars().all(), "pagination": {"next_cursor": None}}


@router.post("", response_model=ResourceEnvelope[ChatSessionResponse], status_code=status.HTTP_201_CREATED)
async def create_chat(payload: ChatCreate, user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Dataset).where(Dataset.id == payload.dataset_id, Dataset.user_id == user.id))
    dataset = result.scalar_one_or_none()
    if dataset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found.")
    if dataset.status != "ready":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Dataset is not ready.")

    chat = ChatSession(user_id=user.id, dataset_id=dataset.id, title="New investigation")
    dataset.status = "locked"
    dataset.locked_at = datetime.now(timezone.utc)
    db.add(chat)
    await db.commit()
    await db.refresh(chat)
    return {"data": chat}


@router.get("/{chat_id}", response_model=ResourceEnvelope[ChatSessionResponse])
async def get_chat(chat_id: str, user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ChatSession).where(ChatSession.id == chat_id, ChatSession.user_id == user.id))
    chat = result.scalar_one_or_none()
    if chat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found.")
    return {"data": chat}
