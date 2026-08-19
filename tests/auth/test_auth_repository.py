import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.auth.repository import AuthRepository
from app.auth.models import RefreshToken
from app.users.models import User

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def repo(mock_session):
    return AuthRepository(session=mock_session)


@pytest.fixture
def sample_user():
    return User(
        id=uuid.uuid4(),
        email="user@example.com",
        first_name="John",
        last_name="Doe",
        hashed_password="hashed-pass",
    )


@pytest.fixture
def sample_token(sample_user):
    return RefreshToken(
        id=uuid.uuid4(),
        user_id=sample_user.id,
        token="refresh-token-value",
    )


class TestGetUser:
    async def test_get_user_by_id_found(self, repo, mock_session, sample_user):
        mock_session.scalar.return_value = sample_user

        result = await repo.get_user_by_id(sample_user.id)
        mock_session.scalar.assert_awaited_once()
        assert result == sample_user

    async def test_get_user_by_id_not_found(self, repo, mock_session):
        mock_session.scalar.return_value = None

        result = await repo.get_user_by_id(uuid.uuid4())
        mock_session.scalar.assert_awaited_once()
        assert result is None

    async def test_get_user_by_email_found(self, repo, mock_session, sample_user):
        mock_session.scalar.return_value = sample_user

        result = await repo.get_user_by_email(sample_user.email)

        mock_session.scalar.assert_awaited_once()
        assert result == sample_user

    async def test_get_user_by_email_not_found(self, repo, mock_session):
        mock_session.scalar.return_value = None

        result = await repo.get_user_by_email("ghost@example.com")

        assert result is None


class TestCreateUser:
    async def test_create_user(self, repo, mock_session, sample_user):
        result = await repo.create_user(sample_user,'hashed_pass')

        mock_session.add.assert_called_once_with(sample_user)
        mock_session.commit.assert_awaited_once()
        mock_session.refresh.assert_awaited_once_with(sample_user)

        assert result == sample_user


class TestSaveOrUpdateToken:
    async def test_save_token_if_none(self, repo, mock_session, sample_user):
        mock_session.scalar.return_value = None

        await repo.save_or_update_token(sample_user.id, "new-token")

        mock_session.add.assert_called_once()
        added_object = mock_session.add.call_args[0][0]
        assert isinstance(added_object, RefreshToken)
        assert added_object.user_id == sample_user.id
        assert added_object.token == 'new-token'
        mock_session.commit.assert_awaited_once()

    async def test_save_token_if_exists(self, repo, mock_session, sample_user, sample_token):
        mock_session.scalar.return_value = sample_token

        await repo.save_or_update_token(sample_user.id, 'updated_token')

        assert sample_token.token == 'updated_token'
        mock_session.add.assert_not_called()
        mock_session.commit.assert_awaited_once()



class TestGetToken:

    async def test_get_token_by_user_id_found(self, repo, mock_session, sample_token):
        mock_session.scalar.return_value = sample_token

        result = await repo.get_token_by_user_id(sample_token.user_id)

        assert result == sample_token

    async def test_get_token_by_user_id_not_found(self, repo, mock_session):
        mock_session.scalar.return_value = None

        result = await repo.get_token_by_user_id(uuid.uuid4())

        assert result is None

    async def test_get_token_found(self, repo, mock_session, sample_token):
        mock_session.scalar.return_value = sample_token

        result = await repo.get_token(sample_token.token)

        assert result == sample_token

    async def test_get_token_not_found(self, repo, mock_session):
        mock_session.scalar.return_value = None

        result = await repo.get_token("unknown-token")

        assert result is None



class TestDeleteToken:

    async def test_delete_token(self, repo, mock_session, sample_token):
        await repo.delete_token(sample_token)

        mock_session.delete.assert_awaited_once_with(sample_token)
        mock_session.commit.assert_awaited_once()

    async def test_delete_user_token_by_id_when_token_exists(self, repo, mock_session, sample_token):
        mock_session.scalar.return_value = sample_token

        await repo.delete_user_token_by_id(sample_token.user_id)

        mock_session.delete.assert_awaited_once_with(sample_token)
        mock_session.commit.assert_awaited_once()

    async def test_delete_user_token_by_id_when_no_token(self, repo, mock_session):
        mock_session.scalar.return_value = None

        await repo.delete_user_token_by_id(uuid.uuid4())

        mock_session.delete.assert_not_called()
        mock_session.commit.assert_not_called()


class TestUpdatePassword:

    async def test_update_password(self, repo, mock_session, sample_user):
        await repo.update_password(sample_user, "new-hashed-pass")

        mock_session.execute.assert_awaited_once()
        mock_session.commit.assert_awaited_once()