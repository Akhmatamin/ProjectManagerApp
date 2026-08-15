import uuid
from abc import ABC, abstractmethod

from app.documents.models import Document


class IDocumentRepository(ABC):
    @abstractmethod
    async def save(self, *args):
        pass

    @abstractmethod
    async def get_by_project_id(self, project_id: uuid.UUID):
        pass

    @abstractmethod
    async def get_by_id(self, document_id: uuid.UUID):
        pass

    @abstractmethod
    async def update(self, document: Document) -> Document:
        pass

    @abstractmethod
    async def delete(self, document: Document):
        pass
