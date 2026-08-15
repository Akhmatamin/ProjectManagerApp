import uuid
from .models import User
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy import select
from .interfaces.repository import IUserRepository
from ..shared.db.database import inject_session


class UserRepository(IUserRepository):
    def __init__(self, session_maker: async_sessionmaker[AsyncSession]):
        self.session_maker = session_maker

    @inject_session
    async def get_by_email(self, email: str, session: AsyncSession = None) -> User | None:
        stmt = select(User).where(User.email == email)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @inject_session
    async def get_by_ids(self, user_ids: list[uuid.UUID], session: AsyncSession = None) -> list[User]:
        stmt = select(User).where(User.id.in_(user_ids))
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @inject_session
    async def get_by_id(self, user_id: uuid.UUID, session: AsyncSession = None) -> User | None:
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
