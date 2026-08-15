from unittest.mock import AsyncMock
import pytest
from app.projects.repository import ProjectInviteRepository


pytestmark = pytest.mark.asyncio


class TestProjectInviteRepository:

    @pytest.fixture
    def redis_client(self):
        return AsyncMock()

    @pytest.fixture
    def invite_repo(self, redis_client):
        return ProjectInviteRepository(redis_client)

    async def test_save_invite_jti(self, invite_repo, redis_client):
        payload = {"project_id": "abc", "permission": "read", "email": "a@gmail.com"}

        await invite_repo.save_invite_jti("jti-1", payload, ttl_seconds=260000)

        redis_client.set.assert_awaited_once()
        args, kwargs = redis_client.set.call_args
        assert args[0] == "invite:jti:jti-1"
        assert "a@gmail.com" in args[1]
        assert kwargs["ex"] == 260000


    async def test_get_invite_jti_found(self, invite_repo, redis_client):
        redis_client.get.return_value = '{"project_id": "abc", "email": "a@gmail.com"}'

        result = await invite_repo.get_invite_jti("jti-1")

        redis_client.get.assert_awaited_once_with("invite:jti:jti-1")
        assert result == {"project_id": "abc", "email": "a@gmail.com"}

    async def test_get_invite_jti_not_found(self, invite_repo, redis_client):
        redis_client.get.return_value = None

        result = await invite_repo.get_invite_jti("not_jti")

        assert result is None

    async def test_delete_invite_jti(self, invite_repo, redis_client):
        await invite_repo.delete_invite_jti("jti-1")

        redis_client.delete.assert_awaited_once_with("invite:jti:jti-1")