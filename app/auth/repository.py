import uuid

import redis.asyncio as redis

from .models import RefreshToken
from app.auth.interfaces.repository import IAuthRepository, IRedisRepository
from app.users.models import User
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy import select, update
from app.shared.db.database import inject_session


class AuthRepository(IAuthRepository):
    def __init__(self, session_maker: async_sessionmaker[AsyncSession]):
        self.session_maker = session_maker

    @inject_session
    async def get_user_by_id(self, user_id: uuid.UUID, session: AsyncSession = None)-> User | None:
        stmt = select(User).where(User.id==user_id)
        return await session.scalar(stmt)

    @inject_session
    async def get_user_by_email(self, email: str, session: AsyncSession = None)-> User | None:
        return await session.scalar(select(User).where(User.email == email))

    @inject_session
    async def create_user(self, db_user: User, hashed_password: str, session: AsyncSession = None)-> User:
        session.add(db_user)
        await session.commit()
        await session.refresh(db_user)
        return db_user

    @inject_session
    async def save_or_update_token(self, user_id:uuid.UUID, token: str, session: AsyncSession = None) -> None:
        existing_token = await self.get_token_by_user_id(user_id, session=session)
        if existing_token:
            existing_token.token = token
        else:
            refresh_token = RefreshToken(
                user_id=user_id,
                token=token,
            )
            session.add(refresh_token)
        await session.commit()

    @inject_session
    async def get_token_by_user_id(self, user_id: uuid.UUID, session: AsyncSession = None)-> RefreshToken | None:
        token = await session.scalar(select(RefreshToken).where(RefreshToken.user_id == user_id))
        return token


    @inject_session
    async def get_token(self, token: str, session: AsyncSession = None) -> RefreshToken | None:
        return await session.scalar(select(RefreshToken).where(RefreshToken.token == token))

    @inject_session
    async def delete_token(self, token: RefreshToken, session: AsyncSession = None) -> None:
        await session.delete(token)
        await session.commit()


    @inject_session
    async def delete_user_token_by_id(self, user_id: uuid.UUID, session: AsyncSession = None) -> None:
        token = await self.get_token_by_user_id(user_id, session=session)
        if token is None:
            return
        await session.delete(token)
        await session.commit()


    @inject_session
    async def update_password(self, user: User, hashed_password: str, session: AsyncSession = None) -> None:
        stmt = update(User).where(User.id==user.id).values(hashed_password=hashed_password)
        await session.execute(stmt)
        await session.commit()



class RedisRepository(IRedisRepository):
    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client

    async def save_code(self, email: str, code: str, expiration_time: int) -> None:
        await self.redis_client.set(f'reset:{email}', code, ex=expiration_time)

    async def get_code(self, email:str)-> str | None:
        return await self.redis_client.get(f'reset:{email}')

    async def delete_code(self, email: str) -> None:
        await self.redis_client.delete(f'reset:{email}')


