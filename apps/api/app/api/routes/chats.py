import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db_session
from app.db.models import AppUser
from app.schemas.chat import ChatCreate, ChatRead, ChatUpdate
from app.schemas.common import DataEnvelope, ListEnvelope
from app.services.chat_service import ChatService


router = APIRouter(prefix="/chats", tags=["Chats"])
chat_service = ChatService()


@router.get("", response_model=ListEnvelope[ChatRead])
async def list_chats(
    user: AppUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    chats = await chat_service.list_chats(session, user)
    return {"data": [ChatRead.model_validate(chat) for chat in chats], "pagination": {"next_cursor": None}}


@router.post("", response_model=DataEnvelope[ChatRead], status_code=status.HTTP_201_CREATED)
async def create_chat(
    payload: ChatCreate,
    user: AppUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> DataEnvelope[ChatRead]:
    chat = await chat_service.create_chat(session, payload, user)
    return DataEnvelope(data=ChatRead.model_validate(chat))


@router.get("/{chat_id}", response_model=DataEnvelope[ChatRead])
async def read_chat(
    chat_id: uuid.UUID,
    user: AppUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> DataEnvelope[ChatRead]:
    chat = await chat_service.get_chat(session, chat_id, user)
    return DataEnvelope(data=ChatRead.model_validate(chat))


@router.patch("/{chat_id}", response_model=DataEnvelope[ChatRead])
async def update_chat(
    chat_id: uuid.UUID,
    payload: ChatUpdate,
    user: AppUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> DataEnvelope[ChatRead]:
    chat = await chat_service.update_chat(session, chat_id, payload, user)
    return DataEnvelope(data=ChatRead.model_validate(chat))


@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat(
    chat_id: uuid.UUID,
    user: AppUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> None:
    await chat_service.delete_chat(session, chat_id, user)
