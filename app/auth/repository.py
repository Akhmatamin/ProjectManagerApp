import uuid

import redis.asyncio as redis

from .models import RefreshToken
from app.auth.interfaces.repository import IAuthRepository, IRedisRepository
from app.users.models import User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update


class AuthRepository(IAuthRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_by_id(self, user_id: uuid.UUID)-> User | None:
        stmt = select(User).where(User.id==user_id)
        return await self.session.scalar(stmt)

    async def get_user_by_email(self, email: str)-> User | None:
        return await self.session.scalar(select(User).where(User.email == email))

    async def create_user(self, db_user: User, hashed_password: str)-> User:
        self.session.add(db_user)
        await self.session.commit()
        await self.session.refresh(db_user)
        return db_user

    async def save_or_update_token(self, user_id:uuid.UUID, token: str) -> None:
        existing_token = await self.get_token_by_user_id(user_id)
        if existing_token:
            existing_token.token = token
        else:
            refresh_token = RefreshToken(
                user_id=user_id,
                token=token,
            )
            self.session.add(refresh_token)
        await self.session.commit()

    async def get_token_by_user_id(self, user_id: uuid.UUID)-> RefreshToken | None:
        token = await self.session.scalar(select(RefreshToken).where(RefreshToken.user_id == user_id))
        return token


    async def get_token(self, token: str) -> RefreshToken | None:
        return await self.session.scalar(select(RefreshToken).where(RefreshToken.token == token))


    async def delete_token(self, token: RefreshToken) -> None:
        await self.session.delete(token)
        await self.session.commit()


    async def delete_user_token_by_id(self, user_id: uuid.UUID) -> None:
        token = await self.get_token_by_user_id(user_id)
        if token is None:
            return
        await self.session.delete(token)
        await self.session.commit()


    async def update_password(self, user: User, hashed_password: str) -> None:
        stmt = update(User).where(User.id==user.id).values(hashed_password=hashed_password)
        await self.session.execute(stmt)
        await self.session.commit()



class RedisRepository(IRedisRepository):
    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client

    async def save_code(self, email: str, code: str, expiration_time: int) -> None:
        await self.redis_client.set(f'reset:{email}', code, ex=expiration_time)

    async def get_code(self, email:str)-> str | None:
        return await self.redis_client.get(f'reset:{email}')

    async def delete_code(self, email: str) -> None:
        await self.redis_client.delete(f'reset:{email}')


