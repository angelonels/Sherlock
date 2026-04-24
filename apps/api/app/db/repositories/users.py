from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AppUser
from app.schemas.auth import ClerkClaims


class UsersRepository:
    async def get_by_clerk_user_id(
        self,
        session: AsyncSession,
        clerk_user_id: str,
    ) -> AppUser | None:
        result = await session.execute(
            select(AppUser).where(
                AppUser.clerk_user_id == clerk_user_id,
                AppUser.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def create_from_clerk_claims(
        self,
        session: AsyncSession,
        claims: ClerkClaims,
    ) -> AppUser:
        user = AppUser(
            clerk_user_id=claims.clerk_user_id,
            email=claims.email,
            first_name=claims.first_name,
            last_name=claims.last_name,
            image_url=claims.image_url,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    async def update_from_clerk_claims(
        self,
        session: AsyncSession,
        user: AppUser,
        claims: ClerkClaims,
    ) -> AppUser:
        user.email = claims.email
        user.first_name = claims.first_name
        user.last_name = claims.last_name
        user.image_url = claims.image_url
        await session.commit()
        await session.refresh(user)
        return user

