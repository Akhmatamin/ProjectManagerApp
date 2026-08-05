import uuid
import redis
from .models import RefreshToken
from .schemas import UserRegisterSchema
from app.auth.interfaces.repository import IAuthRepository, IRedisRepository
from app.users.models import User
from app.shared.config import REDIS_HOST, REDIS_PORT, REDIS_DB
from sqlalchemy.orm import Session
from sqlalchemy import select, update


redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT,db=REDIS_DB, decode_responses=True)


class AuthRepository(IAuthRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_email(self, email: str)-> User | None:
        return self.db.scalar(select(User).where(User.email == email))


    def create_user(self, user_data: UserRegisterSchema, hashed_password: str)-> User:
        db_user = User(
            email=user_data.email,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            hashed_password=hashed_password,
        )

        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def save_or_update_token(self, user_id:uuid.UUID, token: str) -> None:
        existing_token = self.get_token_by_user_id(user_id)
        if existing_token:
            existing_token.token = token
        else:
            refresh_token = RefreshToken(
                user_id=user_id,
                token=token,
            )
            self.db.add(refresh_token)
        self.db.commit()

    def get_token_by_user_id(self, user_id: uuid.UUID)-> RefreshToken | None:
        token = self.db.scalar(select(RefreshToken).where(RefreshToken.user_id == user_id))
        return token

    def get_token(self, token: str) -> RefreshToken | None:
        return self.db.scalar(select(RefreshToken).where(RefreshToken.token == token))

    def delete_token(self, token: RefreshToken) -> None:
        self.db.delete(token)
        self.db.commit()

    def delete_user_token_by_id(self, user_id: uuid.UUID) -> None:
        token = self.get_token_by_user_id(user_id)
        if token is None:
            return
        self.db.delete(token)
        self.db.commit()

    def update_password(self, user: User, hashed_password: str) -> None:
        stmt = update(User).where(User.id==user.id).values(hashed_password=hashed_password)
        self.db.execute(stmt)
        self.db.commit()


class RedisRepository(IRedisRepository):
    def __init__(self, redis_client: redis.Redis = redis_client):
        self.redis_client = redis_client

    def save_code(self, email: str, code: str, expiration_time: int) -> None:
        self.redis_client.set(f'reset:{email}', code, ex=expiration_time)

    def get_code(self, email:str)-> str | None:
        return self.redis_client.get(f'reset:{email}')

    def delete_code(self, email: str) -> None:
        self.redis_client.delete(f'reset:{email}')


