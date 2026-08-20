import uuid
from abc import ABC, abstractmethod

from app.projects.models import Project, ProjectPermission
from app.projects.schemas import ProjectUpdateSchema


class IProjectService(ABC):
    @abstractmethod
    async def create_project(self, project: Project, current_user_id: uuid.UUID):
        pass

    @abstractmethod
    async def get_projects_with_access(self, user_id: uuid.UUID):
        pass

    @abstractmethod
    async def get_project_details(self, project_id: uuid.UUID, current_user: uuid.UUID):
        pass

    @abstractmethod
    async def update_project_details(self, project_id: uuid.UUID, project_data: ProjectUpdateSchema, current_user: uuid.UUID):
        pass

    @abstractmethod
    async def delete_project(self, project_id: uuid.UUID, current_user: uuid.UUID):
        pass

    @abstractmethod
    async def invite_member(self, project_id: uuid.UUID, member_email: str, current_user: uuid.UUID,
                            permission: ProjectPermission):
        pass # Use with email
    @abstractmethod
    async def share_project_link(self, project_id: uuid.UUID, email: str,current_user: uuid.UUID,
                                 permission: ProjectPermission):
        pass

    @abstractmethod
    async def join_project_by_token(self, token: str, current_user: uuid.UUID):
        pass


