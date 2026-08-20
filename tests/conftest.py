from unittest.mock import MagicMock

import pytest

from app.shared.config import Settings


@pytest.fixture
def settings():
    settings = MagicMock(spec=Settings)
    settings.resend_api_key = 'test_key'
    settings.resend_from = 'from@test.com'
    settings.reset_code_expire_seconds = 300
    return settings
