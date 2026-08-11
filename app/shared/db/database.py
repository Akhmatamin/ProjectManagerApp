from app.shared.config import get_settings
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

settings = get_settings()

engine = create_async_engine(settings.database_url)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async def get_db_session():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
