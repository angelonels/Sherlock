from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.db.models import AppUser
from app.schemas.common import DataEnvelope
from app.schemas.user import UserRead


router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=DataEnvelope[UserRead])
async def read_current_user(user: AppUser = Depends(get_current_user)) -> dict[str, UserRead]:
    return {"data": UserRead.model_validate(user)}

