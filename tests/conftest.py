from unittest.mock import MagicMock
import pytest
from app.shared.config import Settings
from app.users.models import User
from app.projects.models import Project
from app.documents.models import Document
from app.auth.models import RefreshToken


@pytest.fixture
def settings():
    settings = MagicMock(spec=Settings)
    settings.resend_api_key = 'test_key'
    settings.resend_from = 'from@test.com'
    settings.reset_code_expire_seconds = 300
    return settings
