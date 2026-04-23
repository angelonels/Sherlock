from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_db_session
from app.db.models import AppUser
from app.services.auth_service import AuthService
from app.services.user_service import UserService


bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> AppUser:
    claims = await AuthService(settings).verify_credentials(credentials)
    return await UserService().get_or_create_from_clerk_claims(session, claims)

