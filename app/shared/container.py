from dependency_injector import containers, providers
import redis.asyncio as redis
from app.shared.db.database import get_db_session
from app.auth.repository import AuthRepository, RedisRepository
from app.shared.config import get_settings
from app.auth.service import AuthService
from app.projects.repository import ProjectRepository, DocumentRepository
from app.projects.service import ProjectService, DocumentService

class Container(containers.DeclarativeContainer):

    wiring_config = containers.WiringConfiguration(
        modules=[
            'app.auth.router',
            'app.projects.router',
            'app.shared.dependencies'
        ]
    )
    config = providers.Singleton(get_settings)

    db_session = providers.Resource(get_db_session)
    redis_client = providers.Singleton(redis.Redis, host=config.provided.redis_host,
                                       port=config.provided.redis_port,
                                       db=config.provided.redis_db, decode_responses=True)

    auth_repository = providers.Factory(AuthRepository, db=db_session)
    redis_repository_auth = providers.Factory(RedisRepository, redis_client=redis_client)

    auth_service = providers.Factory(AuthService, user_repo=auth_repository,
                                     redis_repo=redis_repository_auth, settings=config.provided)

    project_repository = providers.Factory(ProjectRepository, db=db_session)
    project_service = providers.Factory(ProjectService, project_repo=project_repository)

    document_repository = providers.Factory(DocumentRepository, db=db_session)
    document_service = providers.Factory(DocumentService, document_repo=document_repository,
                                         project_repo=project_repository)