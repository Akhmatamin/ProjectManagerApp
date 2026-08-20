from collections.abc import AsyncIterable

from dishka import Provider, Scope, provide
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.auth.interfaces.repository import IAuthRepository, IRedisRepository
from app.auth.interfaces.service import IAuthService, IEmailService
from app.auth.repository import AuthRepository, RedisRepository
from app.auth.service import AuthService, EmailService
from app.documents.interfaces.repository import IDocumentRepository
from app.documents.interfaces.service import IDocumentService, IS3Service
from app.documents.repository import DocumentRepository
from app.documents.service import DocumentService, S3Service
from app.projects.interfaces.repository import (
    IProjectInviteRepository,
    IProjectRepository,
)
from app.projects.interfaces.service import IProjectService
from app.projects.repository import ProjectInviteRepository, ProjectRepository
from app.projects.service import ProjectService
from app.shared.client import ResendAPIClient
from app.shared.config import Settings, get_settings
from app.shared.db.database import create_engine, create_session_maker, session_scope
from app.users.interfaces.repository import IUserRepository
from app.users.repository import UserRepository


class AppProvider(Provider):
    @provide(scope=Scope.APP)
    def get_settings(self) -> Settings:
        return get_settings()

    @provide(scope=Scope.APP)
    def get_engine(self, config: Settings) -> AsyncEngine:
        return create_engine(config.database_url)

    @provide(scope=Scope.APP)
    def get_session_maker(
        self, engine: AsyncEngine
    ) -> async_sessionmaker[AsyncSession]:
        return create_session_maker(engine)

    @provide(scope=Scope.APP)
    def get_redis(self, config: Settings) -> Redis:
        return Redis(
            host=config.redis_host,
            port=config.redis_port,
            db=config.redis_db,
            decode_responses=True,
        )

    @provide(scope=Scope.REQUEST)
    async def get_session(
        self, session_maker: async_sessionmaker[AsyncSession]
    ) -> AsyncIterable[AsyncSession]:
        async with session_scope(session_maker) as session:
            yield session

    resend_client = provide(ResendAPIClient, scope=Scope.APP)
    s3_service = provide(S3Service, provides=IS3Service, scope=Scope.APP)
    email_service = provide(EmailService, provides=IEmailService, scope=Scope.APP)

    auth_repo = provide(AuthRepository, provides=IAuthRepository, scope=Scope.REQUEST)
    user_repo = provide(UserRepository, provides=IUserRepository, scope=Scope.REQUEST)
    project_repo = provide(
        ProjectRepository, provides=IProjectRepository, scope=Scope.REQUEST
    )
    document_repo = provide(
        DocumentRepository, provides=IDocumentRepository, scope=Scope.REQUEST
    )
    redis_repo = provide(
        RedisRepository, provides=IRedisRepository, scope=Scope.REQUEST
    )
    project_invite_repo = provide(
        ProjectInviteRepository, provides=IProjectInviteRepository, scope=Scope.REQUEST
    )

    auth_service = provide(AuthService, provides=IAuthService, scope=Scope.REQUEST)
    project_service = provide(
        ProjectService, provides=IProjectService, scope=Scope.REQUEST
    )
    document_service = provide(
        DocumentService, provides=IDocumentService, scope=Scope.REQUEST
    )
