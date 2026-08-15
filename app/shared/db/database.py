from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker, AsyncEngine
from functools import wraps
from typing import Callable
from contextlib import asynccontextmanager

def create_engine(db_url: str, echo: bool = False):
    return create_async_engine(db_url, echo=echo)

def create_session_maker(engine: AsyncEngine):
    return async_sessionmaker(engine, expire_on_commit=False, autoflush=False)


@asynccontextmanager
async def session_scope(async_session_maker: async_sessionmaker[AsyncSession]):
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


# engine = create_async_engine(settings.database_url)
# AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
# async def get_db_session():
#     async with AsyncSessionLocal() as session:
#         try:
#             yield session
#         finally:
#             await session.close()


def inject_session(repo_method: Callable):
    @wraps(repo_method)
    async def wrapper(self, *args, **kwargs):
        if kwargs.get('session'):
            return await repo_method(self, *args, **kwargs)

        async with session_scope(self.session_maker) as session:
            kwargs['session'] = session
            return await repo_method(self, *args, **kwargs)
    return wrapper
