from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


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
