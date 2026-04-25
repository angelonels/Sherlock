import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ChatCreate(BaseModel):
    dataset_id: uuid.UUID


class ChatUpdate(BaseModel):
    title: str


class ChatRead(BaseModel):
    id: uuid.UUID
    dataset_id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

