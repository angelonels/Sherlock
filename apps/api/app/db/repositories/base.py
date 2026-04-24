from typing import Generic, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base


ModelT = TypeVar("ModelT", bound=Base)


class Repository(Generic[ModelT]):
    model: type[ModelT]

    async def get(self, session: AsyncSession, resource_id: object) -> ModelT | None:
        return await session.get(self.model, resource_id)

