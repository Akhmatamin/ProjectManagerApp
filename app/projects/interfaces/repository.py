import uuid
from abc import ABC, abstractmethod

from app.projects.models import Project, Document
from app.projects.schemas import (ProjectCreateSchema, ProjectUpdateSchema)


class IProjectRepository(ABC):
    @abstractmethod
    async def get_project_by_id(self, project_id: uuid.UUID):
        pass

    @abstractmethod
    async def get_members_by_id(self, user_ids: list[uuid.UUID]):
        pass

    @abstractmethod
    async def save_project(self, *args):
        pass

    @abstractmethod
    async def get_user_projects_by_user_id(self, user_id: uuid.UUID):
        pass

    @abstractmethod
    async def get_project_if_user_member(self, project_id: uuid.UUID, user_id: uuid.UUID):
        pass

    @abstractmethod
    async def update_project(self, project_id: uuid.UUID, project_data: ProjectUpdateSchema, user_id: uuid.UUID):
        pass

    @abstractmethod
    async def delete_project_db(self, project: Project):
        pass


class IDocumentRepository(ABC):
    @abstractmethod
    async def save_document(self, *args):
        pass

    @abstractmethod
    async def get_documents(self, project_id: uuid.UUID):
        pass

    @abstractmethod
    async def get_document_by_id(self, document_id: uuid.UUID):
        pass

    @abstractmethod
    async def update_document_db(self, document, new_file_attached):
        pass

    @abstractmethod
    async def delete_document_db(self, document: Document):
        pass
