import uuid

from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db_session
from app.db.models import AppUser
from app.schemas.common import DataEnvelope, ListEnvelope
from app.schemas.message import MessageCreate, MessageCreateResponse, MessageRead
from app.services.message_service import MessageService


router = APIRouter(prefix="/chats/{chat_id}/messages", tags=["Messages"])
message_service = MessageService()


@router.get("", response_model=ListEnvelope[MessageRead])
async def list_messages(
    chat_id: uuid.UUID,
    user: AppUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    messages = await message_service.list_messages(session, chat_id, user)
    return {"data": [MessageRead.model_validate(message) for message in messages], "pagination": {"next_cursor": None}}


@router.post("", response_model=DataEnvelope[MessageCreateResponse], status_code=status.HTTP_202_ACCEPTED)
async def create_message(
    chat_id: uuid.UUID,
    payload: MessageCreate,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    user: AppUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> DataEnvelope[MessageCreateResponse]:
    message, run = await message_service.create_message(
        session,
        chat_id=chat_id,
        payload=payload,
        idempotency_key=idempotency_key,
        user=user,
    )
    return DataEnvelope(data=MessageCreateResponse(message=MessageRead.model_validate(message), analysis_run_id=run.id))
