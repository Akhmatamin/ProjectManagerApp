import pytest
from unittest.mock import AsyncMock

from app.auth.repository import RedisRepository

pytestmark = pytest.mark.asyncio


class TestRedisRepository:

    @pytest.fixture
    def redis_client(self):
        return AsyncMock()

    @pytest.fixture
    def redis_repo(self, redis_client):
        return RedisRepository(redis_client)

    async def test_save_code(self, redis_repo, redis_client):
        await redis_repo.save_code('user@gmail.com', '1212', expiration_time=300)

        redis_client.set.assert_awaited_once_with('reset:user@gmail.com', '1212', ex=300)

    async def test_get_code_exists(self, redis_repo, redis_client):
        redis_client.get.return_value = '2222'

        result = await redis_repo.get_code('user@gmail.com')

        redis_client.get.assert_awaited_once_with(f'reset:user@gmail.com')
        assert result == '2222'

    async def test_get_code_not_exists(self, redis_repo, redis_client):
        redis_client.get.return_value = None

        result = await redis_repo.get_code('user@gmail.com')

        assert result is None

    async def test_delete_code(self, redis_repo, redis_client):
        await redis_repo.delete_code('user@gmail.com')

        redis_client.delete.assert_awaited_once_with('reset:user@gmail.com')