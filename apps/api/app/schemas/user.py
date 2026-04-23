import uuid

from pydantic import BaseModel, ConfigDict


class UserRead(BaseModel):
    id: uuid.UUID
    email: str | None
    first_name: str | None
    last_name: str | None
    image_url: str | None

    model_config = ConfigDict(from_attributes=True)

