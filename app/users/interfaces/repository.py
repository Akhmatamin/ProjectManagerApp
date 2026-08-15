import uuid
from abc import ABC, abstractmethod
from app.users.models import User


class IUserRepository(ABC):
    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        pass

    @abstractmethod
    async def get_by_ids(self, user_ids: list[uuid.UUID]) -> list[User]:
        pass

    @abstractmethod
    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        pass