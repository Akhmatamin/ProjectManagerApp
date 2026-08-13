import redis.asyncio as redis
from dependency_injector import containers, providers
from app.auth.repository import AuthRepository, RedisRepository
from app.auth.service import AuthService, EmailService
from app.projects.repository import DocumentRepository, ProjectRepository
from app.projects.service import DocumentService, ProjectService
from app.shared.config import get_settings
from app.users.repository import UserRepository


class Container(containers.DeclarativeContainer):

    wiring_config = containers.WiringConfiguration(
        modules=[
            'app.auth.router',
            'app.projects.router',
            'app.shared.dependencies',
        ]
    )
    config = providers.Singleton(get_settings)

    redis_client = providers.Singleton(
        redis.Redis,
        host=config.provided.redis_host,
        port=config.provided.redis_port,
        db=config.provided.redis_db,
        decode_responses=True,
    )

    auth_repository = providers.Factory(AuthRepository)
    user_repository = providers.Factory(UserRepository)
    project_repository = providers.Factory(ProjectRepository)
    document_repository = providers.Factory(DocumentRepository)

    redis_repository_auth = providers.Factory(
        RedisRepository, redis_client=redis_client
    )

    email_service = providers.Singleton(EmailService, settings=config)
    auth_service = providers.Factory(
        AuthService,
        redis_repo=redis_repository_auth,
        settings=config,
        email_service=email_service
    )
    project_service = providers.Factory(ProjectService)
    document_service = providers.Factory(DocumentService)