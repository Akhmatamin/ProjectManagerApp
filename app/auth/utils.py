from datetime import UTC, datetime, timedelta

from app.auth.models import RefreshToken
from app.shared.config import get_settings

settings = get_settings()


def token_expired(token: RefreshToken) -> bool:
    time = datetime.now(UTC) - timedelta(days=settings.refresh_token_lifetime)
    return token.created_at < time
