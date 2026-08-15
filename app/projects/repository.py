import json
import uuid

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.projects.interfaces.repository import IProjectRepository, IProjectInviteRepository
from app.projects.models import Project, ProjectPermission, ProjectMember
from app.projects.schemas import ProjectUpdateSchema
from app.shared.db.database import inject_session


class ProjectRepository(IProjectRepository):
    def __init__(self, session_maker: async_sessionmaker[AsyncSession]):
        self.session_maker = session_maker

    @inject_session
    async def save(self, new_project: Project, session: AsyncSession = None):
        session.add(new_project)
        await session.commit()
        stmt = select(Project).where(Project.id == new_project.id).options(
            selectinload(Project.owner),
            selectinload(Project.documents),
            selectinload(Project.user_memberships).selectinload(ProjectMember.user),
        )
        return await session.scalar(stmt)


    @inject_session
    async def get_by_id(self, project_id: uuid.UUID, load_documents: bool = False, session: AsyncSession = None) -> Project | None:
        options = [
            selectinload(Project.owner),
            selectinload(Project.user_memberships).selectinload(ProjectMember.user),
        ]
        if load_documents:
            options.append(selectinload(Project.documents))

        stmt = select(Project).where(Project.id == project_id).options(*options)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @inject_session
    async def get_by_user_id(self, user_id: uuid.UUID, session: AsyncSession = None):
        stmt = (select(Project).where(Project.user_memberships.any(ProjectMember.user_id == user_id)).options(
            selectinload(Project.owner),
            selectinload(Project.documents),
            selectinload(Project.user_memberships).selectinload(ProjectMember.user),
        ).execution_options(populate_existing=True))
        result = await session.execute(stmt)
        return list(result.scalars().unique().all())

    @inject_session
    async def get_if_user_member(self, project_id: uuid.UUID, user_id: uuid.UUID, session: AsyncSession = None):
        stmt = (select(Project).where(Project.id == project_id,
                                     Project.user_memberships.any(ProjectMember.user_id == user_id)).options(
            selectinload(Project.owner),
            selectinload(Project.user_memberships).selectinload(ProjectMember.user),
            selectinload(Project.documents),
        ).execution_options(populate_existing=True))
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @inject_session
    async def update(self, project_id: uuid.UUID, project_data: ProjectUpdateSchema, user_id: uuid.UUID, session: AsyncSession = None):
        project = await self.get_if_user_member(project_id, user_id, session=session)
        if not project:
            return None

        update_data = project_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(project, key, value)
        await session.commit()
        await session.refresh(project)
        return project

    @inject_session
    async def delete(self, project: Project, session: AsyncSession = None):
        await session.delete(project)
        await session.commit()


    @inject_session
    async def save_members_with_permission(self,project_member: ProjectMember, session: AsyncSession = None):
        session.add(project_member)
        await session.commit()
        await session.refresh(project_member, attribute_names=["user"])
        return project_member

    @inject_session
    async def get_user_permission(self, project_id: uuid.UUID, user_id: uuid.UUID, session: AsyncSession = None) -> ProjectPermission | None:
        stmt = select(ProjectMember.permission).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


class ProjectInviteRepository(IProjectInviteRepository):
    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client
        self.prefix = "invite:jti"
    def _key(self, jti: str):
        return f"{self.prefix}:{jti}"

    async def save_invite_jti(self, jti: str, payload: dict,
                              ttl_seconds: int):
        await self.redis_client.set(self._key(jti), json.dumps(payload, default=str), ex=ttl_seconds)

    async def get_invite_jti(self, jti: str):
        raw_value = await self.redis_client.get(self._key(jti))
        if raw_value is None:
            return None
        return json.loads(raw_value)

    async def delete_invite_jti(self, jti: str):
        await self.redis_client.delete(self._key(jti))
