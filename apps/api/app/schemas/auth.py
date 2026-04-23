from typing import Any

from pydantic import BaseModel, Field


class ClerkClaims(BaseModel):
    clerk_user_id: str = Field(alias="sub")
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    image_url: str | None = None

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "ClerkClaims":
        return cls.model_validate(
            {
                "sub": payload.get("sub"),
                "email": payload.get("email") or payload.get("email_address"),
                "first_name": payload.get("first_name") or payload.get("given_name"),
                "last_name": payload.get("last_name") or payload.get("family_name"),
                "image_url": payload.get("image_url") or payload.get("picture"),
            }
        )

