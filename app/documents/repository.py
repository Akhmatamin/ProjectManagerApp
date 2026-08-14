import uuid
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy import select
from app.documents.interfaces.repository import IDocumentRepository
from app.documents.models import Document
from app.shared.db.database import inject_session



class DocumentRepository(IDocumentRepository):
    def __init__(self, session_maker: async_sessionmaker[AsyncSession]):
        self.session_maker = session_maker

    @inject_session
    async def save(self, new_document: Document, session: AsyncSession = None):
        session.add(new_document)
        await session.commit()
        await session.refresh(new_document)
        return new_document

    @inject_session
    async def get_by_project_id(self, project_id: uuid.UUID, session: AsyncSession = None):
        stmt = select(Document).where(Document.project_id == project_id)
        result = await session.execute(stmt)
        return result.scalars().all()

    @inject_session
    async def get_by_id(self, document_id: uuid.UUID, session: AsyncSession = None):
        stmt = select(Document).where(Document.id == document_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


    @inject_session
    async def update(self, document: Document, session: AsyncSession = None) -> Document:
        session.add(document)
        await session.commit()
        await session.refresh(document)
        return document

    @inject_session
    async def delete(self, document: Document, session: AsyncSession = None):
        await session.delete(document)
        await session.commit()