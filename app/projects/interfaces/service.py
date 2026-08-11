import uuid
from abc import ABC, abstractmethod
from app.projects.schemas import ProjectUpdateSchema
from app.users.models import User
from app.projects.models import Project


class IProjectService(ABC):
    @abstractmethod
    def create_project(self, project: Project, current_user: User):
        pass

    @abstractmethod
    def get_projects_with_access(self, user_id: uuid.UUID):
        pass

    @abstractmethod
    def get_project_details(self, project_id: uuid.UUID, current_user: uuid.UUID):
        pass

    @abstractmethod
    def update_project_details(self, project_id: uuid.UUID, project_data: ProjectUpdateSchema, current_user: uuid.UUID):
        pass

    @abstractmethod
    def delete_project(self, project_id: uuid.UUID, current_user: uuid.UUID):
        pass

    @abstractmethod
    async def invite_member(self, user_id: uuid.UUID, member_email: str, current_user: uuid.UUID):
        pass


class IDocumentService(ABC):
    @abstractmethod
    def upload_document(self, file, project_id: uuid.UUID, current_user_id: uuid.UUID):
        pass

    @abstractmethod
    async def get_all_project_documents(self, project_id: uuid.UUID, current_user_id: uuid.UUID):
        pass

    @abstractmethod
    async def download_document(self, document_id: uuid.UUID, current_user_id: uuid.UUID):
        pass

    @abstractmethod
    async def update_document(self, new_file,document_id: uuid.UUID, current_user_id: uuid.UUID):
        pass

    @abstractmethod
    async def delete_document(self, document_id: uuid.UUID, current_user_id: uuid.UUID):
        pass