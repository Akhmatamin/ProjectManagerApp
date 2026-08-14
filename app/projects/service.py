import uuid

from fastapi import UploadFile
from sqlalchemy_file import File as SQLFile

from app.auth.interfaces.service import IEmailService
from app.projects.interfaces.service import IProjectService, IDocumentService
from app.projects.interfaces.repository import IProjectRepository, IDocumentRepository, IProjectInviteRepository
from app.shared.config import Settings
from app.shared.exceptions import InvalidLink
from app.shared.security import create_invite_token, decode_invite_token
from app.users.interfaces.repository import IUserRepository
from app.projects.models import Project, Document, ProjectMember, ProjectPermission
from app.projects.schemas import ProjectUpdateSchema
from app.projects.exceptions import (ProjectNotFound,
                                     NotMemberOrNoProject, AccessDenied,
                                     DocumentNotFound, UserAlreadyMember, UserNotFound)



class ProjectService(IProjectService):
    def __init__(self, project_repo: IProjectRepository, user_repo: IUserRepository,
                 invite_repo: IProjectInviteRepository, email_service: IEmailService,
                 settings: Settings):
        self.project_repo = project_repo
        self.user_repo = user_repo
        self.invite_repo = invite_repo
        self.email_service = email_service
        self.settings = settings


    async def create_project(self, new_project: Project, current_user_id: uuid.UUID):
        user = await self.user_repo.get_by_id(current_user_id)
        if not user:
            raise UserNotFound()

        new_project.user_memberships.append(
            ProjectMember(user_id=current_user_id, permission=ProjectPermission.WRITE)
        )
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

    async def invite_member(self, project_id: uuid.UUID, member_email: str, current_user: uuid.UUID,
                            permission: ProjectPermission):
        project = await self.project_repo.get_by_id(project_id)
        if not project:
            raise ProjectNotFound()

        if current_user != project.owner_id:
            raise AccessDenied()

        user = await self.user_repo.get_by_email(member_email)
        if not user:
            raise UserNotFound()

        existing_permission = await self.project_repo.get_user_permission(project_id, user.id)
        if existing_permission is not None:
            raise UserAlreadyMember()

        project_member = ProjectMember(
            project_id=project_id,
            user_id=user.id,
            permission=permission
        )

        result = await self.project_repo.save_members_with_permission(project_member)
        return {"message": "Member invited successfully",
                "project_id": result.project_id}



    async def share_project_link(self, project_id: uuid.UUID, email: str, current_user: uuid.UUID,
                                 permission: ProjectPermission):
        project = await self.project_repo.get_by_id(project_id)
        if not project:
            raise ProjectNotFound()
        if current_user != project.owner_id:
            raise AccessDenied()

        token_jti = str(uuid.uuid4())
        ttl_seconds = self.settings.invite_link_expire_seconds

        token = create_invite_token(project_id=project.id,
                                    permission=permission,
                                    jti=token_jti,
                                    expires_in_seconds=ttl_seconds)

        await self.invite_repo.save_invite_jti(jti=token_jti,
                                               payload={
                                                   'project_id': str(project.id),
                                                   'permission': permission.value,
                                                   'email': email,
                                               }, ttl_seconds=ttl_seconds)

        join_link = f"{self.settings.frontend_base_url}?token={token}"
        await self.email_service.send_project_invite(
            email=email, project_name=project.name,join_link=join_link, permission=permission.value
        )
        return {
            "message": f"Email for invite sent to user: {email}"
        }


    async def join_project_by_token(self, token: str, current_user_id: uuid.UUID):
        payload = decode_invite_token(token)

        project_id = uuid.UUID(payload["project_id"])
        permission = ProjectPermission(payload["permission"])
        token_jti = payload.get("jti")

        invite_data = await self.invite_repo.get_invite_jti(token_jti)
        if not invite_data:
            raise InvalidLink("Invite link is invalid, expired, or already used")

        project = await self.project_repo.get_by_id(project_id)
        if not project:
            raise ProjectNotFound()

        user = await self.user_repo.get_by_id(current_user_id)
        if not user:
            raise UserNotFound(message="User not found, please register!")

        invite_email = invite_data.get("email")
        if invite_email and invite_email != user.email:
            raise AccessDenied("This invite link belongs to another user")

        existing_permission = await self.project_repo.get_user_permission(project_id, user.id)
        if existing_permission is not None:
            raise UserAlreadyMember()

        project_member = ProjectMember(
            project_id=project_id,
            user_id=user.id,
            permission=permission
        )
        result = await self.project_repo.save_members_with_permission(project_member)
        await self.invite_repo.delete_invite_jti(jti=token_jti)

        return {
            "message": "You have successfully joined to project",
            "project_id": result.project_id,
        }



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

