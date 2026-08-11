import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.projects.interfaces.repository import IProjectRepository, IDocumentRepository
from app.projects.models import Project, Document
from app.projects.schemas import ProjectUpdateSchema
from app.users.models import User

class ProjectRepository(IProjectRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_email(self, email: str):
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()


    async def get_members_by_id(self, user_ids: list[uuid.UUID]):
        stmt = select(User).where(User.id.in_(user_ids))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())


    async def save_project(self, name: str, description: str, owner_id: uuid.UUID, members: list[User], documents: list[Document]):
        new_project = Project(
            name=name,
            description=description,
            owner_id=owner_id,
            members=members,
            documents=documents,
        )
        self.db.add(new_project)
        await self.db.commit()
        return new_project

    async def get_project_by_id(self,project_id: uuid.UUID, load_documents: bool = False):
        options = [selectinload(Project.members)]
        if load_documents:
            options.append(selectinload(Project.documents))

        stmt = select(Project).where(Project.id == project_id).options(*options)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()


    async def get_user_projects_by_user_id(self, user_id: uuid.UUID):
        stmt = select(Project).where(Project.members.any(User.id == user_id)).options(
            selectinload(Project.documents),
            selectinload(Project.members),
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().unique().all())


    async def get_project_if_user_member(self, project_id: uuid.UUID, user_id: uuid.UUID):
        stmt = (select(Project).where(Project.id == project_id,
                                     Project.members.any(User.id == user_id)).options(
            selectinload(Project.members),
            selectinload(Project.documents),
        ))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_project(self, project_id: uuid.UUID, project_data: ProjectUpdateSchema, user_id: uuid.UUID):
        project = await self.get_project_if_user_member(project_id, user_id)
        if not project:
            return None

        update_data = project_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(project, key, value)
        await self.db.commit()
        await self.db.refresh(project)
        return project


    async def delete_project_db(self, project: Project):
        await self.db.delete(project)
        await self.db.commit()

    # async def get_project_member_by_id(self, project_id: uuid.UUID, member_id: uuid.UUID):
    #     stmt = select(User).where(User.id == member_id, User.members_projects.any(Project.id == project_id))
    #     result = await self.db.execute(stmt)
    #     return result.scalar_one_or_none()


    async def save_members(self, project, member):
        project.members.append(member)
        await self.db.commit()
        await self.db.refresh(project)
        return project


class DocumentRepository(IDocumentRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save_document(self, file_attached, project_id: uuid.UUID):
        new_document = Document(
            file=file_attached,
            project_id=project_id,
        )
        self.db.add(new_document)
        await self.db.commit()
        await self.db.refresh(new_document)
        return new_document

    async def get_documents(self, project_id: uuid.UUID):
        stmt = select(Document).where(Document.project_id == project_id)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_document_by_id(self, document_id: uuid.UUID):
        stmt = select(Document).where(Document.id == document_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_document_db(self, document: Document, new_file_attached):
        document.file = new_file_attached

        self.db.add(document)
        await self.db.commit()
        await self.db.refresh(document)
        return document

    async def delete_document_db(self, document: Document):
        await self.db.delete(document)
        await self.db.commit()