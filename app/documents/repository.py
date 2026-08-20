import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.documents.interfaces.repository import IDocumentRepository
from app.documents.models import Document


class DocumentRepository(IDocumentRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, new_document: Document):
        self.session.add(new_document)
        await self.session.commit()
        await self.session.refresh(new_document)
        return new_document

    async def get_by_project_id(self, project_id: uuid.UUID):
        stmt = select(Document).where(Document.project_id == project_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, document_id: uuid.UUID):
        stmt = select(Document).where(Document.id == document_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


    async def update(self, document: Document) -> Document:
        self.session.add(document)
        await self.session.commit()
        await self.session.refresh(document)
        return document

    async def delete(self, document: Document):
        await self.session.delete(document)
        await self.session.commit()
