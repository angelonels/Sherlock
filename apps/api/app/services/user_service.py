from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AppUser
from app.db.repositories.users import UsersRepository
from app.schemas.auth import ClerkClaims


class UserService:
    def __init__(self, users_repository: UsersRepository | None = None) -> None:
        self.users_repository = users_repository or UsersRepository()

    async def get_or_create_from_clerk_claims(
        self,
        session: AsyncSession,
        claims: ClerkClaims,
    ) -> AppUser:
        user = await self.users_repository.get_by_clerk_user_id(session, claims.clerk_user_id)
        if user is None:
            return await self.users_repository.create_from_clerk_claims(session, claims)

        changed = (
            user.email != claims.email
            or user.first_name != claims.first_name
            or user.last_name != claims.last_name
            or user.image_url != claims.image_url
        )
        if changed:
            return await self.users_repository.update_from_clerk_claims(session, user, claims)
        return user

