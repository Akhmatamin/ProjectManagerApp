from datetime import datetime, timedelta, timezone
from app.shared.config import REFRESH_TOKEN_LIFETIME
from app.auth.models import RefreshToken


def token_expired(token: RefreshToken) -> bool:
    time= datetime.now(timezone.utc) - timedelta(days=REFRESH_TOKEN_LIFETIME)
    return token.created_at < time