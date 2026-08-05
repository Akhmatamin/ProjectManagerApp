# from abc import ABC, abstractmethod
# from typing import Optional
# from app.users.models import User
# from app.users.schemas import UserRegisterSchema
#
# class IUserRepository(ABC):
#     @abstractmethod
#     def get_user_by_email(self, email: str)-> type[User] | None:
#         pass
#
#     @abstractmethod
#     def create_user(self, user_data: UserRegisterSchema, hashed_password: str)-> Optional[User]:
#         pass
