import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.documents.service import DocumentService
from app.documents.models import Document
from app.documents.exceptions import DocumentNotFound
from app.projects.exceptions import NotMemberOrNoProject, AccessDenied
from app.projects.models import ProjectPermission

pytestmark = pytest.mark.asyncio


@pytest.fixture
def document_repo():
    return AsyncMock()


@pytest.fixture
def project_repo():
    return AsyncMock()


@pytest.fixture
def service(document_repo, project_repo):
    return DocumentService(document_repo=document_repo, project_repo=project_repo)


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
    file.read.return_value = b"file-bytes"
    return file


@pytest.fixture
def sample_document(project_id):
    doc = Document(id=uuid.uuid4(), project_id=project_id)
    doc.file = MagicMock()
    return doc


class TestUploadDocument:

    async def test_upload_document_success(self, service, project_repo, document_repo,
                                           sample_project, upload_file, project_id, user_id):
        project_repo.get_user_permission.return_value = ProjectPermission.WRITE
        saved_doc = Document(id=uuid.uuid4(), project_id=project_id)
        document_repo.save.return_value = saved_doc

        with patch("app.documents.service.SQLFile") as mock_sqlfile:
            mock_sqlfile.return_value = "attached-file"
            result = await service.upload_document(upload_file, project_id, user_id)

        project_repo.get_user_permission.assert_awaited_once_with(project_id, user_id)
        upload_file.read.assert_awaited_once()
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

    async def test_upload_document_not_member(self, service, project_repo, document_repo,
                                              upload_file, project_id, user_id):
        project_repo.get_user_permission.return_value = None

        with pytest.raises(NotMemberOrNoProject):
            await service.upload_document(upload_file, project_id, user_id)

        upload_file.read.assert_not_called()
        document_repo.save.assert_not_called()

    async def test_upload_document_read_permission_forbidden(self, service, project_repo, document_repo,
                                                             upload_file, project_id, user_id):
        project_repo.get_user_permission.return_value = ProjectPermission.READ

        with pytest.raises(AccessDenied):
            await service.upload_document(upload_file, project_id, user_id)

        upload_file.read.assert_not_called()
        document_repo.save.assert_not_called()


class TestGetAllProjectDocuments:

    async def test_get_all_project_documents_success(self, service, project_repo, document_repo,
                                                     sample_project, sample_document,
                                                     project_id, user_id):
        project_repo.get_if_user_member.return_value = sample_project
        document_repo.get_by_project_id.return_value = [sample_document]

        result = await service.get_all_project_documents(project_id, user_id)

        document_repo.get_by_project_id.assert_awaited_once_with(project_id)
        assert result == [sample_document]

    async def test_get_all_project_documents_not_member(self, service, project_repo, document_repo,
                                                        project_id, user_id):
        project_repo.get_if_user_member.return_value = None

        with pytest.raises(NotMemberOrNoProject):
            await service.get_all_project_documents(project_id, user_id)

        document_repo.get_by_project_id.assert_not_called()


class TestDownloadDocument:

    async def test_download_document_success(self, service, document_repo, project_repo,
                                             sample_document, sample_project, user_id):
        document_repo.get_by_id.return_value = sample_document
        project_repo.get_if_user_member.return_value = sample_project

        result = await service.download_document(sample_document.id, user_id)

        project_repo.get_if_user_member.assert_awaited_once_with(sample_document.project_id, user_id)
        assert result == sample_document.file

    async def test_download_document_not_found(self, service, document_repo, user_id):
        document_repo.get_by_id.return_value = None

        with pytest.raises(DocumentNotFound):
            await service.download_document(uuid.uuid4(), user_id)

    async def test_download_document_not_member(self, service, document_repo, project_repo,
                                                sample_document, user_id):
        document_repo.get_by_id.return_value = sample_document
        project_repo.get_if_user_member.return_value = None

        with pytest.raises(NotMemberOrNoProject):
            await service.download_document(sample_document.id, user_id)


class TestUpdateDocument:

    async def test_update_document_success(self, service, document_repo, project_repo,
                                           sample_document, sample_project, upload_file, user_id):
        document_repo.get_by_id.return_value = sample_document
        project_repo.get_user_permission.return_value = ProjectPermission.WRITE
        document_repo.update.return_value = sample_document

        with patch("app.documents.service.SQLFile") as mock_sqlfile:
            mock_sqlfile.return_value = "new-attached-file"
            result = await service.update_document(upload_file, sample_document.id, user_id)

        upload_file.read.assert_awaited_once()
        mock_sqlfile.assert_called_once_with(
            content=b"file-bytes", filename="report.pdf", content_type="application/pdf"
        )
        assert sample_document.file == "new-attached-file"
        document_repo.update.assert_awaited_once_with(sample_document)
        assert result == {
            "message": "Document updated successfully",
            "document_id": sample_document.id,
        }

    async def test_update_document_not_found(self, service, document_repo, upload_file, user_id):
        document_repo.get_by_id.return_value = None

        with pytest.raises(DocumentNotFound):
            await service.update_document(upload_file, uuid.uuid4(), user_id)

        upload_file.read.assert_not_called()

    async def test_update_document_not_member(self, service, document_repo, project_repo,
                                              sample_document, upload_file, user_id):
        document_repo.get_by_id.return_value = sample_document
        project_repo.get_user_permission.return_value = None

        with pytest.raises(NotMemberOrNoProject):
            await service.update_document(upload_file, sample_document.id, user_id)

        upload_file.read.assert_not_called()
        document_repo.update.assert_not_called()

    async def test_update_document_read_permission_forbidden(self, service, document_repo, project_repo,
                                                             sample_document, upload_file, user_id):
        document_repo.get_by_id.return_value = sample_document
        project_repo.get_user_permission.return_value = ProjectPermission.READ

        with pytest.raises(AccessDenied):
            await service.update_document(upload_file, sample_document.id, user_id)

        upload_file.read.assert_not_called()
        document_repo.update.assert_not_called()


class TestDeleteDocument:

    async def test_delete_document_success(self, service, document_repo, project_repo,
                                           sample_document, sample_project, user_id):
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

    async def test_delete_document_not_member(self, service, document_repo, project_repo,
                                              sample_document, user_id):
        document_repo.get_by_id.return_value = sample_document
        project_repo.get_if_user_member.return_value = None

        with pytest.raises(NotMemberOrNoProject):
            await service.delete_document(sample_document.id, user_id)

        document_repo.delete.assert_not_called()

    async def test_delete_document_not_owner(self, service, document_repo, project_repo,
                                             sample_document, sample_project, user_id):
        document_repo.get_by_id.return_value = sample_document
        sample_project.owner_id = uuid.uuid4()
        project_repo.get_if_user_member.return_value = sample_project

        with pytest.raises(AccessDenied):
            await service.delete_document(sample_document.id, user_id)

        document_repo.delete.assert_not_called()

