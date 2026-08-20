import uuid
import aioboto3
from fastapi import UploadFile
from sqlalchemy_file import File as SQLFile
from app.documents.interfaces.service import IDocumentService, IS3Service
from app.projects.interfaces.repository import IProjectRepository
from app.documents.interfaces.repository import IDocumentRepository
from app.documents.models import Document
from app.projects.exceptions import NotMemberOrNoProject, AccessDenied, FileKeyMissing
from app.projects.models import ProjectPermission
from app.documents.exceptions import DocumentNotFound, FileTooLarge
from app.shared.config import Settings



class DocumentService(IDocumentService):
    def __init__(self, document_repo: IDocumentRepository, project_repo: IProjectRepository,
                 s3_service: IS3Service):
        self.document_repo = document_repo
        self.project_repo = project_repo
        self.s3_service = s3_service

    @staticmethod
    async def _calculate_size(file: UploadFile):
        max_file_size = 200 * 1024 * 1024
        file_size = file.size
        print(file_size)
        if file_size < max_file_size:
            return True

    async def _ensure_write_permission(self, project_id: uuid.UUID, current_user_id: uuid.UUID):
        permission = await self.project_repo.get_user_permission(project_id, current_user_id)
        if permission is None:
            raise NotMemberOrNoProject()
        if permission != ProjectPermission.WRITE:
            raise AccessDenied("Write permission is required for this operation")


    async def upload_document(self, new_file, project_id: uuid.UUID, current_user_id: uuid.UUID):
        await self._ensure_write_permission(project_id, current_user_id)

        if not await self._calculate_size(new_file):
            raise FileTooLarge()

        file_attached = SQLFile(
            content=new_file.file,
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



    async def download_document(self, document_id: uuid.UUID, current_user_id: uuid.UUID, is_resized: bool = False):
        document = await self.document_repo.get_by_id(document_id)
        if not document:
            raise DocumentNotFound()


        project = await self.project_repo.get_if_user_member(document.project_id, current_user_id)
        if not project:
            raise NotMemberOrNoProject()
        file_object = document.file

        file_key = getattr(file_object, "file_id", None)
        if not file_key:
            file_key = file_object.path.split("/", 1)[-1]
        if not file_key:
            raise FileKeyMissing()
        file_key = str(file_key)

        if is_resized:
            if document.file.content_type in ["image/jpeg", "image/png", "image/jpg"]:
                file_key = f'resized/{file_key}'
            else:
                raise AccessDenied("Only JPEG and PNG images are resized.")


        download_url = await self.s3_service.get_download_url(
            file_key=file_key,
            file_name=file_object.filename,
            content_type=file_object.content_type,
        )

        return {"download_url": download_url,
                'file_key': file_key,
                'file_name': file_object.filename,
                'content_type': file_object.content_type,
                'file_id': file_object.file_id}


    async def update_document(self, new_file: UploadFile, document_id: uuid.UUID, current_user_id: uuid.UUID):
        document = await self.document_repo.get_by_id(document_id)
        if not document:
            raise DocumentNotFound()
        await self._ensure_write_permission(document.project_id, current_user_id)


        document.file = SQLFile(
            content=new_file.file,
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






class S3Service(IS3Service):
    def __init__(self, settings: Settings):
        self.settings = settings
        self.session = aioboto3.Session(
            aws_access_key_id=self.settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=self.settings.AWS_SECRET_ACCESS_KEY,
            region_name=self.settings.AWS_REGION,
        )
        self.bucket = settings.S3_BUCKET_NAME


    # This is for manual approach, but I will use with sqlalchemy-file, to manage files in db also
    async def generate_upload_url(self, file_name: str, content_type: str,
                                  folder: str = 'uploads', expires_in: int = 3600) -> dict:

        file_key = f"{folder}/{uuid.uuid4()}_{file_name}"
        async with self.session.client(
                "s3", region_name=self.settings.AWS_REGION,
                endpoint_url=f"https://s3.{self.settings.AWS_REGION}.amazonaws.com") as s3_client:

            upload_url = await s3_client.generate_presigned_url(
                ClientMethod='put_object',
                Params={
                    'Bucket': self.bucket,
                    'Key': file_key,
                    'ContentType': content_type,
                },
                ExpiresIn=expires_in,
            )
            return {
                'upload_url': upload_url,
                'file_key': file_key,
                'expires_in': f'{expires_in} seconds',
            }


    async def get_download_url(self, file_key: str, file_name: str | None = None,
        content_type: str | None = None,
        expires_in: int = 3600,
    ) -> str:
        async with self.session.client(
                "s3", region_name=self.settings.AWS_REGION,
                endpoint_url=f"https://s3.{self.settings.AWS_REGION}.amazonaws.com") as s3_client:

            params = {'Bucket': self.bucket, 'Key': file_key}
            if file_name:
                params['ResponseContentDisposition'] = f'attachment; filename="{file_name}"'
            if content_type:
                params['ResponseContentType'] = content_type

            url = await s3_client.generate_presigned_url(
                ClientMethod='get_object',
                Params=params,
                ExpiresIn=expires_in,
            )
            return url

