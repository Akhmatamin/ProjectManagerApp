import jwt
import uuid
from dependency_injector.wiring import inject, Provide
from fastapi import Depends, HTTPException, status
from jwt.exceptions import InvalidTokenError
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.interfaces.service import IAuthService
from app.projects.interfaces.service import IProjectService, IDocumentService
from app.shared.db.database import get_db_session
from app.shared.config import Settings
from app.shared.container import Container
from app.users.models import User
token_security = HTTPBearer()


@inject
def get_auth_service(
    db: AsyncSession = Depends(get_db_session),
    auth_repo_factory = Depends(Provide[Container.auth_repository.provider]),
    auth_service_factory = Depends(Provide[Container.auth_service.provider])) -> IAuthService:

    auth_repo = auth_repo_factory(db=db)
    return auth_service_factory(user_repo=auth_repo)

@inject
def get_project_service(
        db: AsyncSession = Depends(get_db_session),
        project_repo_factory = Depends(Provide[Container.project_repository.provider]),
        user_repo_factory = Depends(Provide[Container.user_repository.provider]),
        project_service_factory = Depends(Provide[Container.project_service.provider])) -> IProjectService:

    project_repo = project_repo_factory(db=db)
    user_repo = user_repo_factory(db=db)
    return project_service_factory(project_repo=project_repo, user_repo=user_repo)


@inject
def get_document_service(
        db: AsyncSession = Depends(get_db_session),
        document_repo_factory = Depends(Provide[Container.document_repository.provider]),
        project_repo_factory = Depends(Provide[Container.project_repository.provider]),
        document_service_factory = Depends(Provide[Container.document_service.provider])) -> IDocumentService:

    document_repo = document_repo_factory(db=db)
    project_repo = project_repo_factory(db=db)
    return document_service_factory(document_repo=document_repo, project_repo=project_repo)


@inject
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(token_security),
    db: AsyncSession = Depends(get_db_session),
    auth_repo_factory = Depends(Provide[Container.auth_repository.provider]),
    settings: Settings = Depends(Provide[Container.config])) -> User:

    auth_repo = auth_repo_factory(db=db)

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



