from datetime import datetime, timedelta, timezone
from app.shared.config import get_settings
from app.auth.models import RefreshToken

settings = get_settings()

def token_expired(token: RefreshToken) -> bool:
    time= datetime.now(timezone.utc) - timedelta(days=settings.refresh_token_lifetime)
    return token.created_at < time
