from fastapi import APIRouter, Depends
from api.deps import current_user
from models.user import User
from schemas.common import ResourceEnvelope
from schemas.user import UserResponse


router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=ResourceEnvelope[UserResponse])
async def get_me(user: User = Depends(current_user)):
    return {"data": user}
