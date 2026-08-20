import json
import uuid

import redis.asyncio as redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.projects.interfaces.repository import (
    IProjectInviteRepository,
    IProjectRepository,
)
from app.projects.models import Project, ProjectMember, ProjectPermission
from app.projects.schemas import ProjectUpdateSchema


class ProjectRepository(IProjectRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, new_project: Project):
        self.session.add(new_project)
        await self.session.commit()
        await self.session.refresh(new_project)
        stmt = (
            select(Project)
            .where(Project.id == new_project.id)
            .options(
                selectinload(Project.owner),
                selectinload(Project.documents),
                selectinload(Project.user_memberships).selectinload(ProjectMember.user),
            )
        )
        return await self.session.scalar(stmt)

    async def get_by_id(
        self, project_id: uuid.UUID, load_documents: bool = False
    ) -> Project | None:
        options = [
            selectinload(Project.owner),
            selectinload(Project.user_memberships).selectinload(ProjectMember.user),
        ]
        if load_documents:
            options.append(selectinload(Project.documents))

        stmt = select(Project).where(Project.id == project_id).options(*options)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: uuid.UUID):
        stmt = (
            select(Project)
            .where(Project.user_memberships.any(ProjectMember.user_id == user_id))
            .options(
                selectinload(Project.owner),
                selectinload(Project.documents),
                selectinload(Project.user_memberships).selectinload(ProjectMember.user),
            )
            .execution_options(populate_existing=True)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().unique().all())

    async def get_if_user_member(self, project_id: uuid.UUID, user_id: uuid.UUID):
        stmt = (
            select(Project)
            .where(
                Project.id == project_id,
                Project.user_memberships.any(ProjectMember.user_id == user_id),
            )
            .options(
                selectinload(Project.owner),
                selectinload(Project.user_memberships).selectinload(ProjectMember.user),
                selectinload(Project.documents),
            )
            .execution_options(populate_existing=True)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update(
        self,
        project_id: uuid.UUID,
        project_data: ProjectUpdateSchema,
        user_id: uuid.UUID,
    ):
        project = await self.get_if_user_member(project_id, user_id)
        if not project:
            return None

        update_data = project_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(project, key, value)
        await self.session.commit()
        await self.session.refresh(project)
        return project

    async def delete(self, project: Project):
        await self.session.delete(project)
        await self.session.commit()

    async def save_members_with_permission(self, project_member: ProjectMember):
        self.session.add(project_member)
        await self.session.commit()
        await self.session.refresh(project_member, attribute_names=["user"])
        return project_member

    async def get_user_permission(
        self, project_id: uuid.UUID, user_id: uuid.UUID
    ) -> ProjectPermission | None:
        stmt = select(ProjectMember.permission).where(
            ProjectMember.project_id == project_id, ProjectMember.user_id == user_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class ProjectInviteRepository(IProjectInviteRepository):
    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client
        self.prefix = "invite:jti"

    def _key(self, jti: str):
        return f"{self.prefix}:{jti}"

    async def save_invite_jti(self, jti: str, payload: dict, ttl_seconds: int):
        await self.redis_client.set(
            self._key(jti), json.dumps(payload, default=str), ex=ttl_seconds
        )

    async def get_invite_jti(self, jti: str):
        raw_value = await self.redis_client.get(self._key(jti))
        if raw_value is None:
            return None
        return json.loads(raw_value)

    async def delete_invite_jti(self, jti: str):
        await self.redis_client.delete(self._key(jti))
