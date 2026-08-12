import uuid

from fastapi import UploadFile
from sqlalchemy_file import File as SQLFile
from app.projects.interfaces.service import IProjectService, IDocumentService
from app.projects.interfaces.repository import IProjectRepository, IDocumentRepository
from app.users.interfaces.repository import IUserRepository
from app.projects.models import Project, Document
from app.users.models import User
from app.projects.schemas import ProjectUpdateSchema
from app.projects.exceptions import (ProjectNotFound,
                                     NotMemberOrNoProject, AccessDenied,
                                     DocumentNotFound, UserAlreadyMember, UserNotFound)



class ProjectService(IProjectService):
    def __init__(self, project_repo: IProjectRepository, user_repo: IUserRepository):
        self.project_repo = project_repo
        self.user_repo = user_repo


    async def create_project(self, new_project: Project, current_user: User):
        new_project.members.append(current_user)
        return await self.project_repo.save(new_project)


    async def get_projects_with_access(self, user_id: uuid.UUID):
        projects = await self.project_repo.get_by_user_id(user_id)
        if not projects:
            raise ProjectNotFound()
        return projects


    async def get_project_details(self, project_id: uuid.UUID, current_user: uuid.UUID):
        project = await self.project_repo.get_if_user_member(project_id, current_user)
        if not project:
            raise ProjectNotFound()
        return project

    async def update_project_details(self, project_id: uuid.UUID, project_data: ProjectUpdateSchema, current_user: uuid.UUID):
        updated_project = await self.project_repo.update(project_id, project_data, current_user)
        if not updated_project:
            raise NotMemberOrNoProject()
        return updated_project

    async def delete_project(self, project_id: uuid.UUID, current_user: uuid.UUID):
        project = await self.project_repo.get_by_id(project_id)
        if not project or current_user != project.owner_id:
            raise AccessDenied()

        await self.project_repo.delete(project)
        return {"message": "Project deleted successfully"}

    async def invite_member(self, project_id: uuid.UUID, member_email: str, current_user: uuid.UUID):
        project = await self.project_repo.get_by_id(project_id)
        if not project or current_user != project.owner_id:
            raise NotMemberOrNoProject()

        member = await self.user_repo.get_by_email(member_email)
        if not member:
            raise UserNotFound()

        if member in project.members:
            raise UserAlreadyMember()

        result = await self.project_repo.save_members(project, member)
        return {"message": "Member invited successfully",
                "project": result}



class DocumentService(IDocumentService):
    def __init__(self, document_repo: IDocumentRepository, project_repo: IProjectRepository):
        self.document_repo = document_repo
        self.project_repo = project_repo


    async def upload_document(self, new_file, project_id: uuid.UUID, current_user_id: uuid.UUID):
        project = await self.project_repo.get_if_user_member(project_id, current_user_id)
        if not project:
            raise NotMemberOrNoProject()

        file_bytes = await new_file.read()

        file_attached = SQLFile(
            content=file_bytes,
            filename=new_file.filename,
            content_type=new_file.content_type,
        )

        new_document = Document(
            file=file_attached,
            project_id=project_id,
        )

        result_doc = await self.document_repo.save(new_document)
        return {"message": "Document uploaded successfully",
                "document_id": result_doc.id}

    async def get_all_project_documents(self, project_id: uuid.UUID, current_user_id: uuid.UUID):
        project = await self.project_repo.get_if_user_member(project_id, current_user_id)
        if not project:
            raise NotMemberOrNoProject()

        return await self.document_repo.get_by_project_id(project_id)

    async def download_document(self, document_id: uuid.UUID, current_user_id: uuid.UUID):
        document = await self.document_repo.get_by_id(document_id)
        if not document:
            raise DocumentNotFound()
        project = await self.project_repo.get_if_user_member(document.project_id, current_user_id)
        if not project:
            raise NotMemberOrNoProject()
        return document.file


    async def update_document(self, new_file: UploadFile, document_id: uuid.UUID, current_user_id: uuid.UUID):
        document = await self.document_repo.get_by_id(document_id)
        if not document:
            raise DocumentNotFound()
        project = await self.project_repo.get_if_user_member(document.project_id, current_user_id)
        if not project:
            raise NotMemberOrNoProject()

        file_bytes = await new_file.read()

        document.file = SQLFile(
            content=file_bytes,
            filename=new_file.filename,
            content_type=new_file.content_type,
        )
        updated_doc = await self.document_repo.update(document)
        return {
            "message": "Document updated successfully",
            "document_id": updated_doc.id
        }


    async def delete_document(self, document_id: uuid.UUID, current_user_id: uuid.UUID):
        document = await self.document_repo.get_by_id(document_id)
        if not document:
            raise DocumentNotFound()
        project = await self.project_repo.get_if_user_member(document.project_id, current_user_id)
        if not project:
            raise NotMemberOrNoProject()
        await self.document_repo.delete(document)

        return {"message": "Document deleted successfully"}

