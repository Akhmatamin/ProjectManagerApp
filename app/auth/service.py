import uuid
import random
from .exceptions import (EmailAlreadyExists, InvalidCredentials,
                         InvalidRefreshToken, ExpiredRefreshToken, InvalidPassword,
                         InvalidEmail, InvalidResetCode)
from app.auth.interfaces.repository import IAuthRepository, IRedisRepository
from .schemas import UserRegisterSchema, UserLoginSchema, ChangePasswordSchema
from app.users.models import User
from app.auth.interfaces.service import IAuthService
from .utils import token_expired
from app.shared.security import (get_password_hash, verify_password,
                                 create_access_token, create_refresh_token)
from app.shared.config import RESET_CODE_EXPIRE_SECONDS


class AuthService(IAuthService):
    def __init__(self, user_repo: IAuthRepository, redis_repo: IRedisRepository):
        self.user_repo = user_repo
        self.redis_repo = redis_repo


    def register_user(self, user_data: UserRegisterSchema):
        user_exists = self.user_repo.get_user_by_email(user_data.email)
        if user_exists:
            raise EmailAlreadyExists()
        hashed_password = get_password_hash(user_data.password)
        new_user = self.user_repo.create_user(user_data, hashed_password)
        return new_user


    def login(self, user_data: UserLoginSchema)-> dict:
        user = self.user_repo.get_user_by_email(user_data.email)
        if not user or not verify_password(user_data.password, user.hashed_password):
            raise InvalidCredentials()

        return self._new_token_pair(user.id)


    def logout(self, refresh_token: str) -> None:
        token = self.user_repo.get_token(refresh_token)
        if token is None:
            raise InvalidRefreshToken()

        self.user_repo.delete_token(token)


    def refresh_new_token(self, refresh_token: str) -> dict:
        stored_token = self._get_valid_token(refresh_token)
        return self._new_token_pair(stored_token.user_id)


    def change_password(self, user: User, password_data: ChangePasswordSchema):
        if not verify_password(password_data.old_password, user.hashed_password):
            raise InvalidPassword()

        hashed_password = get_password_hash(password_data.new_password)
        self.user_repo.update_password(user, hashed_password)
        self.user_repo.delete_user_token_by_id(user.id)


    def request_reset_code(self, email: str):
        user = self.user_repo.get_user_by_email(email)
        if not user:
            raise InvalidEmail()

        code = random.randint(1000, 9999)
        self.redis_repo.save_code(email, str(code), expiration_time=RESET_CODE_EXPIRE_SECONDS)

        return {"message": f"Reset code sent to email. Reset code: {code}"}

    def reset_password(self, email: str, code: str, new_password: str):
        stored_code = self.redis_repo.get_code(email)
        if not stored_code or stored_code != code:
            raise InvalidResetCode()

        user = self.user_repo.get_user_by_email(email)
        if not user:
            raise InvalidEmail()

        hashed_password = get_password_hash(new_password)
        self.user_repo.update_password(user, hashed_password)
        self.user_repo.delete_user_token_by_id(user.id)
        self.redis_repo.delete_code(email)
        return {"message": "Your password has been reset!"}


    def _new_token_pair(self, user_id: uuid.UUID) -> dict:
        access_token = create_access_token(data={"sub": str(user_id)})
        new_refresh_token = create_refresh_token(data={"sub": str(user_id)})
        self.user_repo.save_or_update_token(user_id, new_refresh_token)

        return {"access_token": access_token, "refresh_token": new_refresh_token, "token_type": "Bearer"}


    def _get_valid_token(self, refresh_token: str):
        stored_token = self.user_repo.get_token(refresh_token)
        if not stored_token:
            raise InvalidRefreshToken()
        if token_expired(stored_token):
            self.user_repo.delete_token(stored_token)
            raise ExpiredRefreshToken()

        return stored_token


