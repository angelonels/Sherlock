from pydantic import BaseModel
from datetime import datetime

class ChatSessionResponse(BaseModel):
    id: str
    title: str
    original_filename: str
    created_at: datetime

    class Config:
        from_attributes = True  # Allows Pydantic to read the SQLAlchemy object transparently
