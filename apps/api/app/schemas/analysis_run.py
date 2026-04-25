import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.message import MessageRead


class AnalysisRunRead(BaseModel):
    id: uuid.UUID
    chat_session_id: uuid.UUID
    user_message_id: uuid.UUID
    assistant_message_id: uuid.UUID | None
    status: str
    current_stage: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    assistant_message: MessageRead | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
