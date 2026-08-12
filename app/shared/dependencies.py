import jwt
import uuid
from dependency_injector.wiring import inject, Provide
from fastapi import Depends, HTTPException, status
from app.auth.interfaces.repository import IAuthRepository
from app.shared.config import Settings
from app.shared.container import Container
from app.users.models import User
from jwt.exceptions import InvalidTokenError
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


token_security = HTTPBearer()


@inject
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(token_security),
                           auth_repo: IAuthRepository = Depends(Provide[Container.auth_repository]),
                           settings: Settings = Depends(Provide[Container.config])) -> User:

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = uuid.UUID(user_id_str)

    except (InvalidTokenError, ValueError):
        raise credentials_exception

    user = await auth_repo.get_user_by_id(user_id)
    if user is None:
        raise credentials_exception
    return user