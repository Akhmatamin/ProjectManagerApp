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


@pytest.fixture
def user_repo():
    return AsyncMock(spec=IAuthRepository)


@pytest.fixture
def redis_repo():
    return AsyncMock(spec=IRedisRepository)


@pytest.fixture
def email_service():
    return AsyncMock()


@pytest.fixture
def service(user_repo, redis_repo, settings, email_service):
    return AuthService(
        user_repo=user_repo,
        redis_repo=redis_repo,
        settings=settings,
        email_service=email_service,
    )


@pytest.fixture
def sample_user():
    return User(id=uuid.uuid4(), email='test@gmail.com',
                first_name='test_first_name', last_name='test_last_name',
                hashed_password='hashed-pass', )


class TestRegisterUser:

    async def test_register_user_success(self, service, user_repo):
        user_repo.get_user_by_email.return_value = None
        user_repo.create_user.return_value = User(
            id=uuid.uuid4(), email='test@gmail.com', first_name='test_first_name',
            last_name='test_last_name', hashed_password='hashed-pass'
        )
        data = UserRegisterSchema(
            email='test@gmail.com', first_name='test_first_name', last_name='test_last_name',
            password='new-password'
        )
        with patch('app.auth.service.get_password_hash', new=AsyncMock(return_value='new-password')):
            result = await service.register_user(data)

        user_repo.get_user_by_email.assert_awaited_once_with('test@gmail.com')
        user_repo.create_user.assert_awaited_once()
        assert result.email == 'test@gmail.com'

    async def test_register_user_email_exists(self, service, user_repo, sample_user):
        user_repo.get_user_by_email.return_value = sample_user
        data = UserRegisterSchema(
            email=sample_user.email, first_name='test_first_name', last_name='test_last_name',
            password='new-password'
        )
        with pytest.raises(EmailAlreadyExists):
            await service.register_user(data)

        user_repo.create_user.assert_not_awaited()


class TestLogin:
    async def test_login_success(self, service, user_repo, sample_user):
        user_repo.get_user_by_email.return_value = sample_user
        data = UserLoginSchema(email=sample_user.email, password='pass')

        with patch('app.auth.service.verify_password', new=AsyncMock(return_value=True)), \
            patch('app.auth.service.create_access_token', new=AsyncMock(return_value='access')),\
            patch('app.auth.service.create_refresh_token', new=AsyncMock(return_value='refresh')):
            result = await service.login(data)

        assert result == {
            'access_token': 'access',
            'refresh_token': 'refresh',
            'token_type': 'Bearer',
        }

        user_repo.save_or_update_token.assert_awaited_once_with(sample_user.id, 'refresh')


    async def test_login_user_not_found(self, service, user_repo):
        user_repo.get_user_by_email.return_value = None
        data = UserLoginSchema(email='test@gmail.com', password='password')

        with pytest.raises(InvalidCredentials):
            await service.login(data)

    async def test_login_wrong_password(self, service, user_repo, sample_user):
        user_repo.get_user_by_email.return_value = sample_user
        data = UserLoginSchema(email=sample_user.email, password='wrong_pass')

        with patch('app.auth.service.verify_password', new=AsyncMock(return_value=False)):
            with pytest.raises(InvalidCredentials):
                await service.login(data)


class TestLogout:
    async def test_logout_success(self, service, user_repo):
        token_object = MagicMock()
        user_repo.get_token.return_value = token_object

        await service.logout('refresh_token')
        user_repo.get_token.assert_awaited_once_with('refresh_token')
        user_repo.delete_token.assert_awaited_once_with(token_object)

    async def test_logout_user_not_found(self, service, user_repo):
        user_repo.get_token.return_value = None

        with pytest.raises(InvalidRefreshToken):
            await service.logout('refresh_token')

        user_repo.delete_token.assert_not_awaited()


class TestRefreshNewToken:
    async def test_refresh_new_token_success(self, service, user_repo):
        stored_token = MagicMock()
        stored_token.user_id = uuid.uuid4()
        user_repo.get_token.return_value = stored_token

        with patch('app.auth.service.token_expired', return_value=False), \
                patch('app.auth.service.create_access_token', new=AsyncMock(return_value='access')),\
                patch('app.auth.service.create_refresh_token', new=AsyncMock(return_value='refresh')):
            result = await service.refresh_new_token('old-refresh-token')

        assert result['access_token'] == 'access'
        assert result['refresh_token'] == 'refresh'
        user_repo.save_or_update_token.assert_awaited_once_with(stored_token.user_id, 'refresh')

    async def test_refresh_new_token_not_found(self, service, user_repo):
        user_repo.get_token.return_value = None

        with pytest.raises(InvalidRefreshToken):
            await service.refresh_new_token('old-refresh-token')

        user_repo.save_or_update_token.assert_not_awaited()

    async def test_refresh_new_token_expired(self, service, user_repo):
        stored_token = MagicMock()
        stored_token.user_id = uuid.uuid4()
        user_repo.get_token.return_value = stored_token

        with patch('app.auth.service.token_expired', return_value=True):
            with pytest.raises(ExpiredRefreshToken):
                await service.refresh_new_token('old-refresh-token')

        user_repo.save_or_update_token.assert_not_awaited()
        user_repo.delete_token.assert_awaited_once_with(stored_token)


class TestChangePassword:
    async def test_change_password_success(self, service, user_repo, sample_user):
        data = ChangePasswordSchema(old_password='old-pass', new_password='new-pass')

        with patch('app.auth.service.verify_password', new=AsyncMock(return_value=True)), \
            patch('app.auth.service.get_password_hash', new=AsyncMock(return_value='new-pass')):
            await service.change_password(sample_user, data)

        user_repo.update_password.assert_awaited_once_with(sample_user, 'new-pass')
        user_repo.delete_user_token_by_id.assert_awaited_once_with(sample_user.id)

    async def test_change_password_invalid_old_password(self, service, user_repo, sample_user):
        data = ChangePasswordSchema(old_password='wrong-old-pass', new_password='new-pass')

        with patch('app.auth.service.verify_password', new=AsyncMock(return_value=False)):
            with pytest.raises(InvalidPassword):
                await service.change_password(sample_user, data)

        user_repo.update_password.assert_not_awaited()


class TestRequestResetCode:
    async def test_request_reset_code_success(self, service, user_repo, redis_repo,
                                              email_service, settings, sample_user):
        user_repo.get_user_by_email.return_value = sample_user

        with patch('app.auth.service.random.randint', return_value=1212):
            result = await service.request_reset_code(sample_user.email)

        email_service.send_reset_code.assert_awaited_once_with(sample_user.email, '1212')
        redis_repo.save_code.assert_awaited_once_with(sample_user.email, '1212',
                                                      expiration_time=settings.reset_code_expire_seconds)
        assert '1212' in result['message']

    async def test_request_reset_code_wrong_email(self, service, user_repo,
                                                  email_service):
        user_repo.get_user_by_email.return_value = None

        with pytest.raises(InvalidEmail):
            await service.request_reset_code("test@gmail.com")

        email_service.send_reset_code.assert_not_called()

class TestResetPassword:
    async def test_reset_password_success(self, service, user_repo,
                                          redis_repo,sample_user):

        redis_repo.get_code.return_value = '1111'
        user_repo.get_user_by_email.return_value = sample_user

        with patch('app.auth.service.get_password_hash', new=AsyncMock(return_value='new-pass')):
            result = await service.reset_password(sample_user.email, '1111', 'new-pass')

        user_repo.update_password.assert_awaited_once_with(sample_user, 'new-pass')
        user_repo.delete_user_token_by_id.assert_awaited_once_with(sample_user.id)
        redis_repo.delete_code.assert_awaited_once_with(sample_user.email)
        assert result == {"message": "Your password has been reset!"}

    async def test_reset_password_no_code_in_redis(self, service, redis_repo):
        redis_repo.get_code.return_value = None

        with pytest.raises(InvalidResetCode):
            await service.reset_password("test@example.com", "1234", "new-pass")

    async def test_reset_password_wrong_code(self, service, redis_repo):
        redis_repo.get_code.return_value = "9999"

        with pytest.raises(InvalidResetCode):
            await service.reset_password("test@example.com", "1234", "new-pass")

    async def test_reset_password_wrong_email(self, service, redis_repo, user_repo):
        redis_repo.get_code.return_value = "1234"
        user_repo.get_user_by_email.return_value = None

        with pytest.raises(InvalidEmail):
            await service.reset_password("test@example.com", "1234", "new-pass")