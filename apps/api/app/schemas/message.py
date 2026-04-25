import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class MessageCreate(BaseModel):
    content: str


class MessageRead(BaseModel):
    id: uuid.UUID
    chat_session_id: uuid.UUID
    message_index: int
    role: str
    content: str | None
    blocks: list[dict[str, Any]] | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageCreateResponse(BaseModel):
    message: MessageRead
    analysis_run_id: uuid.UUID
