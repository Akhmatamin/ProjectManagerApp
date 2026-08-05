from abc import ABC, abstractmethod
from app.auth.schemas import UserRegisterSchema, UserLoginSchema, ChangePasswordSchema
from app.users.models import User


class IAuthService(ABC):
    @abstractmethod
    def register_user(self, user_data: UserRegisterSchema)-> dict:
        pass

    @abstractmethod
    def login(self, user_data: UserLoginSchema)-> dict:
        pass

    @abstractmethod
    def logout(self, refresh_token: str):
        pass

    @abstractmethod
    def refresh_new_token(self, refresh_token: str)-> dict:
        pass

    @abstractmethod
    def change_password(self, user: User, password_data: ChangePasswordSchema)-> dict:
        pass

    @abstractmethod
    def request_reset_code(self, email: str):
        pass

    @abstractmethod
    def reset_password(self, email: str, code: str, new_password: str):
        pass