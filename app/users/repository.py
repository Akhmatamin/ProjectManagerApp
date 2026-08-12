import uuid
from .models import User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .interfaces.repository import IUserRepository

class UserRepository(IUserRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()


    async def get_by_ids(self, user_ids: list[uuid.UUID]) -> list[User]:
        stmt = select(User).where(User.id.in_(user_ids))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
