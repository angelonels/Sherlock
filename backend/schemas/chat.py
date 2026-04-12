from pydantic import BaseModel
from datetime import datetime

class ChatSessionResponse(BaseModel):
    id: str
    dataset_id: str
    title: str
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True  # Allows Pydantic to read the SQLAlchemy object transparently
