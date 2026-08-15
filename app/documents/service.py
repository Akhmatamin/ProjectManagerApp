import uuid

from fastapi import UploadFile
from sqlalchemy_file import File as SQLFile
from app.documents.interfaces.service import IDocumentService
from app.projects.interfaces.repository import IProjectRepository
from app.documents.interfaces.repository import IDocumentRepository
from app.documents.models import Document
from app.projects.exceptions import NotMemberOrNoProject, AccessDenied
from app.projects.models import ProjectPermission
from app.documents.exceptions import DocumentNotFound



class DocumentService(IDocumentService):
    def __init__(self, document_repo: IDocumentRepository, project_repo: IProjectRepository):
        self.document_repo = document_repo
        self.project_repo = project_repo

    async def _ensure_write_permission(self, project_id: uuid.UUID, current_user_id: uuid.UUID):
        permission = await self.project_repo.get_user_permission(project_id, current_user_id)
        if permission is None:
            raise NotMemberOrNoProject()
        if permission != ProjectPermission.WRITE:
            raise AccessDenied("Write permission is required for this operation")


    async def upload_document(self, new_file, project_id: uuid.UUID, current_user_id: uuid.UUID):
        await self._ensure_write_permission(project_id, current_user_id)

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
        await self._ensure_write_permission(document.project_id, current_user_id)

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
        if current_user_id != project.owner_id:
            raise AccessDenied("Only project owner can delete documents")
        await self.document_repo.delete(document)

        return {"message": "Document deleted successfully"}

