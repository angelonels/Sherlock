from datetime import datetime
from pydantic import BaseModel


class MessageCreate(BaseModel):
    content: str


class MessageResponse(BaseModel):
    id: str
    chat_session_id: str
    message_index: int
    role: str
    content: str | None = None
    blocks: list[dict] | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class AnalysisRunResponse(BaseModel):
    id: str
    chat_session_id: str
    user_message_id: str
    assistant_message_id: str | None = None
    status: str
    current_stage: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None

    class Config:
        from_attributes = True
