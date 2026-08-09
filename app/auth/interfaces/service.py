from abc import ABC, abstractmethod
from app.auth.schemas import UserRegisterSchema, UserLoginSchema, ChangePasswordSchema
from app.users.models import User


class IAuthService(ABC):
    @abstractmethod
    async def register_user(self, user_data: UserRegisterSchema)-> dict:
        pass

    @abstractmethod
    async def login(self, user_data: UserLoginSchema)-> dict:
        pass

    @abstractmethod
    async def logout(self, refresh_token: str):
        pass

    @abstractmethod
    async def refresh_new_token(self, refresh_token: str)-> dict:
        pass

    @abstractmethod
    async def change_password(self, user: User, password_data: ChangePasswordSchema)-> dict:
        pass

    @abstractmethod
    async def request_reset_code(self, email: str):
        pass

    @abstractmethod
    async def reset_password(self, email: str, code: str, new_password: str):
        pass