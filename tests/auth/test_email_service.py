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


    async def test_send_code(self, email_settings):
        service = EmailService(email_settings)

        with patch('app.auth.service.resend.Emails.send', return_value={'id': 'email1'}) as mock_send:
            result = await service.send_reset_code('user@gmail.com', '1234')

        mock_send.assert_called_once()
        called_params = mock_send.call_args[0][0]

        assert called_params['to'] == ['user@gmail.com']
        assert '1234' in called_params['html']
        assert result == {'id': 'email1'}

    async def test_send_project_invite(self, email_settings):
        service = EmailService(email_settings)

        with patch('app.auth.service.resend.Emails.send', return_value={'id': 'email2'}) as mock_send:
            result = await service.send_project_invite(
                'test@gmail.com', 'project name',
                'http://localhost:3000/join', 'write')

            mock_send.assert_called_once()
            called_params = mock_send.call_args[0][0]
            assert called_params['to'] == ['test@gmail.com']
            assert 'project name' in called_params['html']
            assert 'write' in called_params['html']
            assert result == {'id': 'email2'}
            
