import uuid
from abc import ABC, abstractmethod
from app.auth.schemas import UserRegisterSchema
from app.users.models import User
from app.auth.models import RefreshToken

class IAuthRepository(ABC):
    @abstractmethod
    async def get_user_by_email(self, email: str)-> User | None:
        pass

    @abstractmethod
    async def create_user(self, user_data: UserRegisterSchema, hashed_password: str)-> User | None:
        pass

    @abstractmethod
    async def save_or_update_token(self, user_id: uuid.UUID, token: str)-> RefreshToken | None:
        pass

    @abstractmethod
    async def get_token(self, token: str)-> RefreshToken | None:
        pass

    @abstractmethod
    async def delete_token(self, token: RefreshToken)-> None:
        pass

    @abstractmethod
    async def delete_user_token_by_id(self, user_id: uuid.UUID)-> None:
        pass

    @abstractmethod
    async def update_password(self, user: User, hashed_password: str)-> None:
        pass

class IRedisRepository(ABC):
    @abstractmethod
    async def save_code(self, email: str, code: str, expiration_time: int) -> None:
        pass

    @abstractmethod
    async def get_code(self, email: str) -> str | None:
        pass

    @abstractmethod
    async def delete_code(self, email: str) -> None:
        pass

