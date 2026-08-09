from dependency_injector import containers, providers
from app.shared.db.database import get_db_session
from app.auth.repository import AuthRepository, RedisRepository, redis_client_default
from app.auth.service import AuthService

class Container(containers.DeclarativeContainer):

    wiring_config = containers.WiringConfiguration(
        modules=[
            'app.auth.router'
        ]
    )
    db_session = providers.Resource(get_db_session)

    auth_repository = providers.Factory(AuthRepository, db=db_session)
    redis_repository_auth = providers.Factory(RedisRepository, redis_client=providers.Object(redis_client_default))

    auth_service = providers.Factory(AuthService, user_repo=auth_repository, redis_repo=redis_repository_auth)
