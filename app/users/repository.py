import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .interfaces.repository import IUserRepository
from .models import User


class UserRepository(IUserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_ids(self, user_ids: list[uuid.UUID]) -> list[User]:
        stmt = select(User).where(User.id.in_(user_ids))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
