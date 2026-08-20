import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.documents.exceptions import DocumentNotFound, FileTooLarge
from app.documents.models import Document
from app.documents.service import DocumentService
from app.projects.exceptions import AccessDenied, NotMemberOrNoProject
from app.projects.models import ProjectPermission

pytestmark = pytest.mark.asyncio


@pytest.fixture
def document_repo():
    return AsyncMock()


@pytest.fixture
def project_repo():
    return AsyncMock()


@pytest.fixture
def s3_service():
    return AsyncMock()


@pytest.fixture
def service(document_repo, project_repo, s3_service):
    return DocumentService(
        document_repo=document_repo, project_repo=project_repo, s3_service=s3_service
    )


@pytest.fixture
def project_id():
    return uuid.uuid4()


@pytest.fixture
def user_id():
    return uuid.uuid4()


@pytest.fixture
def sample_project(project_id):
    return MagicMock(id=project_id)


@pytest.fixture
def upload_file():
    file = AsyncMock()
    file.filename = "report.pdf"
    file.content_type = "application/pdf"
    file.size = 1024
    file.file = b"file-bytes"
    file.read.return_value = b"file-bytes"
    return file


@pytest.fixture
def sample_document(project_id):
    doc = Document(id=uuid.uuid4(), project_id=project_id)
    doc.file = MagicMock()
    return doc


class TestUploadDocument:
    async def test_upload_document_success(
        self,
        service,
        project_repo,
        document_repo,
        sample_project,
        upload_file,
        project_id,
        user_id,
    ):
        project_repo.get_user_permission.return_value = ProjectPermission.WRITE
        saved_doc = Document(id=uuid.uuid4(), project_id=project_id)
        document_repo.save.return_value = saved_doc

        with patch("app.documents.service.SQLFile") as mock_sqlfile:
            mock_sqlfile.return_value = "attached-file"
            result = await service.upload_document(upload_file, project_id, user_id)

        project_repo.get_user_permission.assert_awaited_once_with(project_id, user_id)
        mock_sqlfile.assert_called_once_with(
            content=b"file-bytes", filename="report.pdf", content_type="application/pdf"
        )
        document_repo.save.assert_awaited_once()
        saved_arg = document_repo.save.call_args[0][0]
        assert saved_arg.project_id == project_id
        assert saved_arg.file == "attached-file"
        assert result == {
            "message": "Document uploaded successfully",
            "document_id": saved_doc.id,
        }

    async def test_upload_document_file_too_large(
        self, service, project_repo, document_repo, upload_file, project_id, user_id
    ):
        project_repo.get_user_permission.return_value = ProjectPermission.WRITE
        upload_file.size = 201 * 1024 * 1024

        with pytest.raises(FileTooLarge):
            await service.upload_document(upload_file, project_id, user_id)

        document_repo.save.assert_not_called()

    async def test_upload_document_not_member(
        self, service, project_repo, document_repo, upload_file, project_id, user_id
    ):
        project_repo.get_user_permission.return_value = None

        with pytest.raises(NotMemberOrNoProject):
            await service.upload_document(upload_file, project_id, user_id)

        upload_file.read.assert_not_called()
        document_repo.save.assert_not_called()

    async def test_upload_document_read_permission_forbidden(
        self, service, project_repo, document_repo, upload_file, project_id, user_id
    ):
        project_repo.get_user_permission.return_value = ProjectPermission.READ

        with pytest.raises(AccessDenied):
            await service.upload_document(upload_file, project_id, user_id)

        upload_file.read.assert_not_called()
        document_repo.save.assert_not_called()


class TestGetAllProjectDocuments:
    async def test_get_all_project_documents_success(
        self,
        service,
        project_repo,
        document_repo,
        sample_project,
        sample_document,
        project_id,
        user_id,
    ):
        project_repo.get_if_user_member.return_value = sample_project
        document_repo.get_by_project_id.return_value = [sample_document]

        result = await service.get_all_project_documents(project_id, user_id)

        document_repo.get_by_project_id.assert_awaited_once_with(project_id)
        assert result == [sample_document]

    async def test_get_all_project_documents_not_member(
        self, service, project_repo, document_repo, project_id, user_id
    ):
        project_repo.get_if_user_member.return_value = None

        with pytest.raises(NotMemberOrNoProject):
            await service.get_all_project_documents(project_id, user_id)

        document_repo.get_by_project_id.assert_not_called()


class TestDownloadDocument:
    async def test_download_document_success(
        self,
        service,
        document_repo,
        project_repo,
        sample_document,
        sample_project,
        user_id,
    ):
        sample_document.file.file_id = "uploads/file-123"
        sample_document.file.filename = "report.pdf"
        sample_document.file.content_type = "application/pdf"
        document_repo.get_by_id.return_value = sample_document
        project_repo.get_if_user_member.return_value = sample_project
        service.s3_service.get_download_url.return_value = (
            "https://example.com/download"
        )

        result = await service.download_document(sample_document.id, user_id)

        project_repo.get_if_user_member.assert_awaited_once_with(
            sample_document.project_id, user_id
        )
        service.s3_service.get_download_url.assert_awaited_once_with(
            file_key="uploads/file-123",
            file_name="report.pdf",
            content_type="application/pdf",
        )
        assert result == {
            "download_url": "https://example.com/download",
            "file_key": "uploads/file-123",
            "file_name": "report.pdf",
            "content_type": "application/pdf",
            "file_id": "uploads/file-123",
        }

    async def test_download_document_success_resized_image(
        self,
        service,
        document_repo,
        project_repo,
        sample_document,
        sample_project,
        user_id,
    ):
        sample_document.file.file_id = "uploads/image-123"
        sample_document.file.filename = "image.jpg"
        sample_document.file.content_type = "image/jpeg"
        document_repo.get_by_id.return_value = sample_document
        project_repo.get_if_user_member.return_value = sample_project
        service.s3_service.get_download_url.return_value = (
            "https://example.com/download-image"
        )

        result = await service.download_document(
            sample_document.id, user_id, is_resized=True
        )

        service.s3_service.get_download_url.assert_awaited_once_with(
            file_key="resized/uploads/image-123",
            file_name="image.jpg",
            content_type="image/jpeg",
        )
        assert result["file_key"] == "resized/uploads/image-123"

    async def test_download_document_resized_non_image_forbidden(
        self,
        service,
        document_repo,
        project_repo,
        sample_document,
        sample_project,
        user_id,
    ):
        sample_document.file.file_id = "uploads/file-123"
        sample_document.file.filename = "report.pdf"
        sample_document.file.content_type = "application/pdf"
        document_repo.get_by_id.return_value = sample_document
        project_repo.get_if_user_member.return_value = sample_project

        with pytest.raises(AccessDenied, match="Only JPEG and PNG images are resized"):
            await service.download_document(
                sample_document.id, user_id, is_resized=True
            )

    async def test_download_document_not_found(self, service, document_repo, user_id):
        document_repo.get_by_id.return_value = None

        with pytest.raises(DocumentNotFound):
            await service.download_document(uuid.uuid4(), user_id)

    async def test_download_document_not_member(
        self, service, document_repo, project_repo, sample_document, user_id
    ):
        document_repo.get_by_id.return_value = sample_document
        project_repo.get_if_user_member.return_value = None

        with pytest.raises(NotMemberOrNoProject):
            await service.download_document(sample_document.id, user_id)


class TestUpdateDocument:
    async def test_update_document_success(
        self,
        service,
        document_repo,
        project_repo,
        sample_document,
        sample_project,
        upload_file,
        user_id,
    ):
        document_repo.get_by_id.return_value = sample_document
        project_repo.get_user_permission.return_value = ProjectPermission.WRITE
        document_repo.update.return_value = sample_document

        with patch("app.documents.service.SQLFile") as mock_sqlfile:
            mock_sqlfile.return_value = "new-attached-file"
            result = await service.update_document(
                upload_file, sample_document.id, user_id
            )

        mock_sqlfile.assert_called_once_with(
            content=b"file-bytes", filename="report.pdf", content_type="application/pdf"
        )
        assert sample_document.file == "new-attached-file"
        document_repo.update.assert_awaited_once_with(sample_document)
        assert result == {
            "message": "Document updated successfully",
            "document_id": sample_document.id,
        }

    async def test_update_document_not_found(
        self, service, document_repo, upload_file, user_id
    ):
        document_repo.get_by_id.return_value = None

        with pytest.raises(DocumentNotFound):
            await service.update_document(upload_file, uuid.uuid4(), user_id)

        upload_file.read.assert_not_called()

    async def test_update_document_not_member(
        self,
        service,
        document_repo,
        project_repo,
        sample_document,
        upload_file,
        user_id,
    ):
        document_repo.get_by_id.return_value = sample_document
        project_repo.get_user_permission.return_value = None

        with pytest.raises(NotMemberOrNoProject):
            await service.update_document(upload_file, sample_document.id, user_id)

        upload_file.read.assert_not_called()
        document_repo.update.assert_not_called()

    async def test_update_document_read_permission_forbidden(
        self,
        service,
        document_repo,
        project_repo,
        sample_document,
        upload_file,
        user_id,
    ):
        document_repo.get_by_id.return_value = sample_document
        project_repo.get_user_permission.return_value = ProjectPermission.READ

        with pytest.raises(AccessDenied):
            await service.update_document(upload_file, sample_document.id, user_id)

        upload_file.read.assert_not_called()
        document_repo.update.assert_not_called()


class TestDeleteDocument:
    async def test_delete_document_success(
        self,
        service,
        document_repo,
        project_repo,
        sample_document,
        sample_project,
        user_id,
    ):
        document_repo.get_by_id.return_value = sample_document
        sample_project.owner_id = user_id
        project_repo.get_if_user_member.return_value = sample_project

        result = await service.delete_document(sample_document.id, user_id)

        document_repo.delete.assert_awaited_once_with(sample_document)
        assert result == {"message": "Document deleted successfully"}

    async def test_delete_document_not_found(self, service, document_repo, user_id):
        document_repo.get_by_id.return_value = None

        with pytest.raises(DocumentNotFound):
            await service.delete_document(uuid.uuid4(), user_id)

        document_repo.delete.assert_not_called()

    async def test_delete_document_not_member(
        self, service, document_repo, project_repo, sample_document, user_id
    ):
        document_repo.get_by_id.return_value = sample_document
        project_repo.get_if_user_member.return_value = None

        with pytest.raises(NotMemberOrNoProject):
            await service.delete_document(sample_document.id, user_id)

        document_repo.delete.assert_not_called()

    async def test_delete_document_not_owner(
        self,
        service,
        document_repo,
        project_repo,
        sample_document,
        sample_project,
        user_id,
    ):
        document_repo.get_by_id.return_value = sample_document
        sample_project.owner_id = uuid.uuid4()
        project_repo.get_if_user_member.return_value = sample_project

        with pytest.raises(AccessDenied):
            await service.delete_document(sample_document.id, user_id)

        document_repo.delete.assert_not_called()
