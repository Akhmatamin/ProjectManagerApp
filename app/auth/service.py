import random
import uuid

from app.auth.interfaces.repository import IAuthRepository, IRedisRepository
from app.auth.interfaces.service import IAuthService, IEmailService
from app.shared.config import Settings
from app.shared.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)
from app.users.models import User

from ..shared.client import ResendAPIClient
from .exceptions import (
    EmailAlreadyExists,
    ExpiredRefreshToken,
    InvalidCredentials,
    InvalidEmail,
    InvalidPassword,
    InvalidRefreshToken,
    InvalidResetCode,
)
from .schemas import ChangePasswordSchema, UserLoginSchema, UserRegisterSchema
from .utils import token_expired


class EmailService(IEmailService):
    def __init__(self, settings: Settings, resend_client: ResendAPIClient):
        self.settings = settings
        self.resend_client = resend_client

    async def send_reset_code(self, email: str, code: str):
        html_content = f"<p>Your verification code is: <strong>{code}</strong></p>"
        return await self.resend_client.send_email(
            to_email=email,
            subject="Verification code",
            html_content=html_content,
        )

    async def send_project_invite(self, email: str, project_name: str,
                                  join_link:str, permission: str):

        html_content = (
            f"<p>You were invited to project <strong>{project_name}</strong>.</p>"
            f"<p>Permission: <strong>{permission}</strong></p>"
            f"<p><a href='{join_link}'>Join project</a></p>"
        )

        return await self.resend_client.send_email(
            to_email=email,
            subject=f"Invitation to join project {project_name}",
            html_content=html_content,
        )



class AuthService(IAuthService):
    def __init__(self, user_repo: IAuthRepository, redis_repo: IRedisRepository,
                 settings: Settings, email_service: IEmailService):
        self.user_repo = user_repo
        self.redis_repo = redis_repo
        self.settings = settings
        self.email_service = email_service

    async def register_user(self, user_data: UserRegisterSchema)-> User | None:
        user_exists = await self.user_repo.get_user_by_email(user_data.email)
        if user_exists:
            raise EmailAlreadyExists()
        hashed_password = await get_password_hash(user_data.password)

        db_user = User(
            email=user_data.email,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            hashed_password=hashed_password,
        )
        new_user = await self.user_repo.create_user(db_user, hashed_password)
        return new_user


    async def login(self, user_data: UserLoginSchema)-> dict:
        user = await self.user_repo.get_user_by_email(user_data.email)
        if not user or not await verify_password(user_data.password, user.hashed_password):
            raise InvalidCredentials()

        return await self._new_token_pair(user.id)


    async def logout(self, refresh_token: str) -> None:
        token = await self.user_repo.get_token(refresh_token)
        if token is None:
            raise InvalidRefreshToken()

        await self.user_repo.delete_token(token)


    async def refresh_new_token(self, refresh_token: str) -> dict:
        stored_token = await self._get_valid_token(refresh_token)
        return await self._new_token_pair(stored_token.user_id)


    async def change_password(self, user: User, password_data: ChangePasswordSchema) -> None:
        if not await verify_password(password_data.old_password, user.hashed_password):
            raise InvalidPassword()

        hashed_password = await get_password_hash(password_data.new_password)
        await self.user_repo.update_password(user, hashed_password)
        await self.user_repo.delete_user_token_by_id(user.id)


    async def request_reset_code(self, email: str)-> dict:
        user = await self.user_repo.get_user_by_email(email)
        if not user:
            raise InvalidEmail()

        code = random.randint(1000, 9999)
        await self.email_service.send_reset_code(email, str(code))
        await self.redis_repo.save_code(email, str(code), expiration_time=self.settings.reset_code_expire_seconds)

        return {"message": "Reset code sent to email."}

    async def reset_password(self, email: str, code: str, new_password: str) -> dict:
        stored_code = await self.redis_repo.get_code(email)
        if not stored_code or stored_code != code:
            raise InvalidResetCode()

        user = await self.user_repo.get_user_by_email(email)
        if not user:
            raise InvalidEmail()

        hashed_password = await get_password_hash(new_password)
        await self.user_repo.update_password(user, hashed_password)
        await self.user_repo.delete_user_token_by_id(user.id)
        await self.redis_repo.delete_code(email)
        return {"message": "Your password has been reset!"}



    async def _new_token_pair(self, user_id: uuid.UUID) -> dict:
        access_token = await create_access_token(data={"sub": str(user_id)})
        new_refresh_token = await create_refresh_token(data={"sub": str(user_id)})
        await self.user_repo.save_or_update_token(user_id, new_refresh_token)

        return {"access_token": access_token, "refresh_token": new_refresh_token, "token_type": "Bearer"}


    async def _get_valid_token(self, refresh_token: str):
        stored_token = await self.user_repo.get_token(refresh_token)
        if not stored_token:
            raise InvalidRefreshToken()
        if token_expired(stored_token):
            await self.user_repo.delete_token(stored_token)
            raise ExpiredRefreshToken()

        return stored_token

