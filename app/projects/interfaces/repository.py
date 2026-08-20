import uuid
from abc import ABC, abstractmethod

from app.projects.models import Project, ProjectMember, ProjectPermission
from app.projects.schemas import ProjectUpdateSchema


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
    async def update(
        self,
        project_id: uuid.UUID,
        project_data: ProjectUpdateSchema,
        user_id: uuid.UUID,
    ):
        pass

    @abstractmethod
    async def delete(self, project: Project):
        pass

    # @abstractmethod
    # async def save_members(self, project: Project, member: User):
    #     pass
    @abstractmethod
    async def save_members_with_permission(self, project_member: ProjectMember):
        pass

    @abstractmethod
    async def get_user_permission(
        self, project_id: uuid.UUID, user_id: uuid.UUID
    ) -> ProjectPermission | None:
        pass


class IProjectInviteRepository(ABC):
    @abstractmethod
    async def save_invite_jti(self, jti: str, payload: dict, ttl_seconds: int):
        pass

    @abstractmethod
    async def get_invite_jti(self, jti: str):
        pass

    @abstractmethod
    async def delete_invite_jti(self, jti: str):
        pass
