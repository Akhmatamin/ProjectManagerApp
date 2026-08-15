import redis.asyncio as redis
from dependency_injector import containers, providers
from app.auth.repository import AuthRepository, RedisRepository
from app.auth.service import AuthService, EmailService
from app.documents.service import DocumentService
from app.documents.repository import DocumentRepository
from app.projects.repository import ProjectRepository, ProjectInviteRepository
from app.projects.service import ProjectService
from app.shared.config import get_settings
from app.users.repository import UserRepository
from app.shared.db.database import create_session_maker, create_engine


class Container(containers.DeclarativeContainer):

    wiring_config = containers.WiringConfiguration(
        modules=[
            'app.auth.router',
            'app.projects.router',
            'app.documents.router',
            'app.shared.dependencies',
        ]
    )
    config = providers.Singleton(get_settings)

    db_engine = providers.Singleton(create_engine, db_url=config.provided.database_url)
    session_maker = providers.Singleton(create_session_maker, engine=db_engine)


    redis_client = providers.Singleton(
        redis.Redis,
        host=config.provided.redis_host,
        port=config.provided.redis_port,
        db=config.provided.redis_db,
        decode_responses=True,
    )

    auth_repository = providers.Factory(AuthRepository, session_maker=session_maker)
    user_repository = providers.Factory(UserRepository, session_maker=session_maker)
    project_repository = providers.Factory(ProjectRepository, session_maker=session_maker)
    document_repository = providers.Factory(DocumentRepository, session_maker=session_maker)

    redis_repository = providers.Factory(
        RedisRepository, redis_client=redis_client
    )
    project_invite_repository = providers.Factory(ProjectInviteRepository,
                                                  redis_client=redis_client)

    email_service = providers.Singleton(EmailService, settings=config)
    auth_service = providers.Factory(
        AuthService, user_repo=auth_repository,
        redis_repo=redis_repository,
        settings=config,
        email_service=email_service
    )
    project_service = providers.Factory(ProjectService, project_repo=project_repository,
                                        user_repo=user_repository, invite_repo=project_invite_repository,
                                        email_service=email_service, settings=config)
    document_service = providers.Factory(DocumentService, document_repo=document_repository,
                                         project_repo=project_repository)