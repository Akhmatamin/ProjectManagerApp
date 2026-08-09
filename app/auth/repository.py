import uuid
import redis.asyncio as redis
from .models import RefreshToken
from .schemas import UserRegisterSchema
from app.auth.interfaces.repository import IAuthRepository, IRedisRepository
from app.users.models import User
from app.shared.config import REDIS_HOST, REDIS_PORT, REDIS_DB
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update


redis_client_default = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)


class AuthRepository(IAuthRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_email(self, email: str)-> User | None:
        return await self.db.scalar(select(User).where(User.email == email))


    async def create_user(self, user_data: UserRegisterSchema, hashed_password: str)-> User:
        db_user = User(
            email=user_data.email,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            hashed_password=hashed_password,
        )

        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
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
            self.db.add(refresh_token)
        await self.db.commit()

    async def get_token_by_user_id(self, user_id: uuid.UUID)-> RefreshToken | None:
        token = await self.db.scalar(select(RefreshToken).where(RefreshToken.user_id == user_id))
        return token

    async def get_token(self, token: str) -> RefreshToken | None:
        return await self.db.scalar(select(RefreshToken).where(RefreshToken.token == token))

    async def delete_token(self, token: RefreshToken) -> None:
        await self.db.delete(token)
        await self.db.commit()

    async def delete_user_token_by_id(self, user_id: uuid.UUID) -> None:
        token = await self.get_token_by_user_id(user_id)
        if token is None:
            return
        await self.db.delete(token)
        await self.db.commit()

    async def update_password(self, user: User, hashed_password: str) -> None:
        stmt = update(User).where(User.id==user.id).values(hashed_password=hashed_password)
        await self.db.execute(stmt)
        await self.db.commit()


class RedisRepository(IRedisRepository):
    def __init__(self, redis_client: redis.Redis = redis_client_default):
        self.redis_client = redis_client

    async def save_code(self, email: str, code: str, expiration_time: int) -> None:
        await self.redis_client.set(f'reset:{email}', code, ex=expiration_time)

    async def get_code(self, email:str)-> str | None:
        return await self.redis_client.get(f'reset:{email}')

    async def delete_code(self, email: str) -> None:
        await self.redis_client.delete(f'reset:{email}')


