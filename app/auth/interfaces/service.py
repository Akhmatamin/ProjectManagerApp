from abc import ABC, abstractmethod

from app.auth.schemas import ChangePasswordSchema, UserLoginSchema, UserRegisterSchema
from app.users.models import User


class IAuthService(ABC):
    @abstractmethod
    async def register_user(self, user_data: UserRegisterSchema) -> User | None:
        pass

    @abstractmethod
    async def login(self, user_data: UserLoginSchema) -> dict:
        pass

    @abstractmethod
    async def logout(self, refresh_token: str) -> None:
        pass

    @abstractmethod
    async def refresh_new_token(self, refresh_token: str) -> dict:
        pass

    @abstractmethod
    async def change_password(
        self, user: User, password_data: ChangePasswordSchema
    ) -> None:
        pass

    @abstractmethod
    async def request_reset_code(self, email: str) -> dict:
        pass

    @abstractmethod
    async def reset_password(self, email: str, code: str, new_password: str) -> dict:
        pass


class IEmailService(ABC):
    @abstractmethod
    async def send_reset_code(self, email: str, code: str):
        pass

    @abstractmethod
    async def send_project_invite(
        self, email: str, project_name: str, join_link: str, permission: str
    ):
        pass
