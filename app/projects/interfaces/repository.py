import uuid
from abc import ABC, abstractmethod

from app.projects.models import Project, Document
from app.projects.schemas import (ProjectUpdateSchema)
from app.users.models import User


class IProjectRepository(ABC):
    @abstractmethod
    async def get_by_id(self, project_id: uuid.UUID, load_documents: bool = False):
        pass

    @abstractmethod
    async def save(self, new_project: Project):
        pass

    @abstractmethod
    async def get_by_user_id(self, user_id: uuid.UUID):
        pass

    @abstractmethod
    async def get_if_user_member(self, project_id: uuid.UUID, user_id: uuid.UUID):
        pass

    @abstractmethod
    async def update(self, project_id: uuid.UUID, project_data: ProjectUpdateSchema, user_id: uuid.UUID):
        pass

    @abstractmethod
    async def delete(self, project: Project):
        pass

    @abstractmethod
    async def save_members(self, project: Project, member: User):
        pass


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
