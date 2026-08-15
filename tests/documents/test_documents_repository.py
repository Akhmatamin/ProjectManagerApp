import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.documents.repository import DocumentRepository
from app.documents.models import Document

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_session():
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    return mock_session


@pytest.fixture
def repo():
    return DocumentRepository(session_maker=MagicMock())


@pytest.fixture
def sample_document():
    return Document(id=uuid.uuid4(), project_id=uuid.uuid4())


class TestSave:

    async def test_save(self, repo, mock_session, sample_document):
        result = await repo.save(sample_document, session=mock_session)

        mock_session.add.assert_called_once_with(sample_document)
        mock_session.commit.assert_awaited_once()
        mock_session.refresh.assert_awaited_once_with(sample_document)
        assert result == sample_document


class TestGetByProjectId:

    async def test_get_by_project_id_returns_list(self, repo, mock_session, sample_document):
        scalars_result = MagicMock()
        scalars_result.all.return_value = [sample_document]
        exec_result = MagicMock()
        exec_result.scalars.return_value = scalars_result
        mock_session.execute.return_value = exec_result

        result = await repo.get_by_project_id(sample_document.project_id, session=mock_session)

        mock_session.execute.assert_awaited_once()
        assert result == [sample_document]

    async def test_get_by_project_id_empty(self, repo, mock_session):
        scalars_result = MagicMock()
        scalars_result.all.return_value = []
        exec_result = MagicMock()
        exec_result.scalars.return_value = scalars_result
        mock_session.execute.return_value = exec_result

        result = await repo.get_by_project_id(uuid.uuid4(), session=mock_session)

        assert result == []


class TestGetById:

    async def test_get_by_id_found(self, repo, mock_session, sample_document):
        exec_result = MagicMock()
        exec_result.scalar_one_or_none.return_value = sample_document
        mock_session.execute.return_value = exec_result

        result = await repo.get_by_id(sample_document.id, session=mock_session)

        assert result == sample_document

    async def test_get_by_id_not_found(self, repo, mock_session):
        exec_result = MagicMock()
        exec_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = exec_result

        result = await repo.get_by_id(uuid.uuid4(), session=mock_session)

        assert result is None


class TestUpdate:

    async def test_update(self, repo, mock_session, sample_document):
        result = await repo.update(sample_document, session=mock_session)

        mock_session.add.assert_called_once_with(sample_document)
        mock_session.commit.assert_awaited_once()
        mock_session.refresh.assert_awaited_once_with(sample_document)
        assert result == sample_document


class TestDelete:

    async def test_delete(self, repo, mock_session, sample_document):
        await repo.delete(sample_document, session=mock_session)

        mock_session.delete.assert_awaited_once_with(sample_document)
        mock_session.commit.assert_awaited_once()