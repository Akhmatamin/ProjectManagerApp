import uuid

import jwt
from dishka.integrations.fastapi import FromDishka, inject
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError

from app.auth.interfaces.repository import IAuthRepository
from app.shared.config import Settings
from app.users.models import User

token_security = HTTPBearer()


@inject
async def get_current_user(
    auth_repo: FromDishka[IAuthRepository],
    settings: FromDishka[Settings],
    credentials: HTTPAuthorizationCredentials = Depends(token_security),
) -> User:

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        user_id_str = payload.get("sub")
        if not isinstance(user_id_str, str):
            raise credentials_exception
        user_id = uuid.UUID(user_id_str)

    except (InvalidTokenError, ValueError):
        raise credentials_exception

    user = await auth_repo.get_user_by_id(user_id)
    if user is None:
        raise credentials_exception
    return user



