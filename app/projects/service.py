import uuid

from fastapi import UploadFile
from sqlalchemy_file import File as SQLFile
from app.projects.interfaces.service import IProjectService, IDocumentService
from app.projects.interfaces.repository import IProjectRepository, IDocumentRepository
from app.projects.models import Project
from app.users.models import User
from app.projects.schemas import ProjectUpdateSchema
from app.projects.exceptions import (ProjectNotFound,
                                     NotMemberOrNoProject, AccessDenied,
                                     DocumentNotFound, UserAlreadyMember, UserNotFound)



class ProjectService(IProjectService):
    def __init__(self, project_repo: IProjectRepository):
        self.project_repo = project_repo


    async def create_project(self, new_project: Project, current_user: User):
        new_project.members.append(current_user)
        return await self.project_repo.save_project(new_project)


    async def get_projects_with_access(self, user_id: uuid.UUID):
        projects = await self.project_repo.get_user_projects_by_user_id(user_id)
        if not projects:
            raise ProjectNotFound()
        return projects

    async def get_project_details(self, project_id: uuid.UUID, current_user: uuid.UUID):
        project = await self.project_repo.get_project_if_user_member(project_id, current_user)
        if not project:
            raise ProjectNotFound()
        return project

    async def update_project_details(self, project_id: uuid.UUID, project_data: ProjectUpdateSchema, current_user: uuid.UUID):
        updated_project = await self.project_repo.update_project(project_id, project_data, current_user)
        if not updated_project:
            raise NotMemberOrNoProject()
        return updated_project

    async def delete_project(self, project_id: uuid.UUID, current_user: uuid.UUID):
        project = await self.project_repo.get_project_by_id(project_id)
        if not project or current_user != project.owner_id:
            raise AccessDenied()

        await self.project_repo.delete_project_db(project)
        return {"message": "Project deleted successfully"}

    async def invite_member(self, project_id: uuid.UUID, member_email: str, current_user: uuid.UUID):
        project = await self.project_repo.get_project_by_id(project_id)
        if not project or current_user != project.owner_id:
            raise NotMemberOrNoProject()

        member = await self.project_repo.get_user_by_email(member_email)
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


    async def upload_document(self, upload_file, project_id: uuid.UUID, current_user_id: uuid.UUID):
        project = await self.project_repo.get_project_if_user_member(project_id, current_user_id)
        if not project:
            raise NotMemberOrNoProject()

        file_attached = SQLFile(
            content=upload_file.file,
            filename=upload_file.filename,
            content_type=upload_file.content_type,
        )

        doc = await self.document_repo.save_document(file_attached, project_id)
        return {"message": "Document uploaded successfully",
                "document_id": doc.id}

    async def get_all_project_documents(self, project_id: uuid.UUID, current_user_id: uuid.UUID):
        project = await self.project_repo.get_project_if_user_member(project_id, current_user_id)
        if not project:
            raise NotMemberOrNoProject()

        return await self.document_repo.get_documents(project_id)

    async def download_document(self, document_id: uuid.UUID, current_user_id: uuid.UUID):
        document = await self.document_repo.get_document_by_id(document_id)
        if not document:
            raise DocumentNotFound()
        project = await self.project_repo.get_project_if_user_member(document.project_id, current_user_id)
        if not project:
            raise NotMemberOrNoProject()
        return document.file


    async def update_document(self, new_file: UploadFile, document_id: uuid.UUID, current_user_id: uuid.UUID):
        document = await self.document_repo.get_document_by_id(document_id)
        if not document:
            raise DocumentNotFound()
        project = await self.project_repo.get_project_if_user_member(document.project_id, current_user_id)
        if not project:
            raise NotMemberOrNoProject()

        new_file_attached = SQLFile(
            content=new_file.file,
            filename=new_file.filename,
            content_type=new_file.content_type,
        )
        doc = await self.document_repo.update_document_db(document, new_file_attached)

        return {
            "message": "Document updated successfully",
            "document_id": doc.id
        }

    async def delete_document(self, document_id: uuid.UUID, current_user_id: uuid.UUID):
        document = await self.document_repo.get_document_by_id(document_id)
        if not document:
            raise DocumentNotFound()
        project = await self.project_repo.get_project_if_user_member(document.project_id, current_user_id)
        if not project:
            raise NotMemberOrNoProject()
        await self.document_repo.delete_document_db(document)

        return {"message": "Document deleted successfully"}

