import uuid
from sys import path

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.auth.service import AuthService, EmailService
from app.auth.interfaces.repository import IAuthRepository, IRedisRepository
from app.auth.exceptions import (
    EmailAlreadyExists,
    InvalidCredentials,
    InvalidRefreshToken,
    ExpiredRefreshToken,
    InvalidPassword,
    InvalidEmail,
    InvalidResetCode,
)
from app.auth.schemas import UserRegisterSchema, UserLoginSchema, ChangePasswordSchema
from app.projects.exceptions import UserNotFound
from app.users.models import User
from app.users.interfaces.repository import IUserRepository

pytestmark = pytest.mark.asyncio




class TestEmailService:
    @pytest.fixture
    def email_settings(self):
        settings = MagicMock()
        settings.resend_api_key = "test-key"
        settings.resend_from = "emailfrom@example.com"
        return settings

    @pytest.fixture
    def resend_client(self):
        client = AsyncMock()
        client.send_email.return_value = {"id": "email1"}
        return client


    async def test_send_code(self, email_settings, resend_client):
        service = EmailService(email_settings, resend_client)

        result = await service.send_reset_code('user@gmail.com', '1234')

        resend_client.send_email.assert_awaited_once()
        assert resend_client.send_email.call_args.kwargs["to_email"] == "user@gmail.com"
        assert "1234" in resend_client.send_email.call_args.kwargs["html_content"]
        assert result == {"id": "email1"}

    async def test_send_project_invite(self, email_settings, resend_client):
        resend_client.send_email.return_value = {"id": "email2"}
        service = EmailService(email_settings, resend_client)

        result = await service.send_project_invite(
            'test@gmail.com', 'project name',
            'http://localhost:3000/join', 'write')

        resend_client.send_email.assert_awaited_once()
        assert resend_client.send_email.call_args.kwargs["to_email"] == "test@gmail.com"
        assert "project name" in resend_client.send_email.call_args.kwargs["html_content"]
        assert "write" in resend_client.send_email.call_args.kwargs["html_content"]
        assert result == {"id": "email2"}

