import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.projects.repository import ProjectRepository
from app.projects.models import Project, ProjectMember, ProjectPermission
from app.projects.schemas import ProjectUpdateSchema

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_session():
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    return mock_session


@pytest.fixture
def repo(mock_session):
    return ProjectRepository(session=mock_session)


@pytest.fixture
def owner_id():
    return uuid.uuid4()


@pytest.fixture
def sample_project(owner_id):
    project = Project(id=uuid.uuid4(), name="My Project", owner_id=owner_id)
    project.user_memberships = []
    return project


class TestSave:

    async def test_save(self, repo, mock_session, sample_project):
        mock_session.scalar.return_value = sample_project

        result = await repo.save(sample_project)

        mock_session.add.assert_called_once_with(sample_project)
        mock_session.commit.assert_awaited_once()
        mock_session.scalar.assert_awaited_once()
        assert result == sample_project


class TestGetProjectById:

    async def test_get_by_id_found(self, repo, mock_session, sample_project):
        execute_result = MagicMock()
        execute_result.scalar_one_or_none.return_value = sample_project
        mock_session.execute.return_value = execute_result

        result = await repo.get_by_id(sample_project.id)

        mock_session.execute.assert_awaited_once()
        assert result == sample_project

    async def test_get_by_id_not_found(self, repo, mock_session):
        execute_result = MagicMock()
        execute_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = execute_result

        result = await repo.get_by_id(uuid.uuid4())

        assert result is None

    async def test_get_by_id_with_load_documents(self, repo, mock_session, sample_project):
        execute_result = MagicMock()
        execute_result.scalar_one_or_none.return_value = sample_project
        mock_session.execute.return_value = execute_result

        result = await repo.get_by_id(sample_project.id, load_documents=True)

        mock_session.execute.assert_awaited_once()

        assert result == sample_project


class TestGetProjectsByUserId:

    async def test_get_by_user_id_returns_list(self, repo, mock_session, sample_project):
        scalars_result = MagicMock()
        scalars_result.unique.return_value.all.return_value = [sample_project]
        execute_result = MagicMock()
        execute_result.scalars.return_value = scalars_result
        mock_session.execute.return_value = execute_result

        result = await repo.get_by_user_id(uuid.uuid4())

        assert result == [sample_project]

    async def test_get_by_user_id_returns_empty_list(self, repo, mock_session):
        scalars_result = MagicMock()
        scalars_result.unique.return_value.all.return_value = []
        execute_result = MagicMock()
        execute_result.scalars.return_value = scalars_result
        mock_session.execute.return_value = execute_result

        result = await repo.get_by_user_id(uuid.uuid4())

        assert result == []


class TestGetProjectIfUserMember:
    async def test_get_if_user_member_found(self, repo, mock_session, sample_project):
        execute_result = MagicMock()
        execute_result.scalar_one_or_none.return_value = sample_project
        mock_session.execute.return_value = execute_result

        result = await repo.get_if_user_member(sample_project.id, uuid.uuid4())

        assert result == sample_project

    async def test_get_if_user_member_not_found(self, repo, mock_session):
        execute_result = MagicMock()
        execute_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = execute_result

        result = await repo.get_if_user_member(uuid.uuid4(), uuid.uuid4())

        assert result is None


class TestUpdateProject:

    async def test_update_success(self, repo, mock_session, sample_project):
        exec_result = MagicMock()
        exec_result.scalar_one_or_none.return_value = sample_project
        mock_session.execute.return_value = exec_result

        data = ProjectUpdateSchema(name="renamed project", description="updated description")
        result = await repo.update(sample_project.id, data, uuid.uuid4())

        assert sample_project.name == "renamed project"
        assert sample_project.description == "updated description"
        mock_session.commit.assert_awaited_once()
        mock_session.refresh.assert_awaited_once_with(sample_project)
        assert result == sample_project

    async def test_update_no_access_returns_none(self, repo, mock_session):
        exec_result = MagicMock()
        exec_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = exec_result

        data = ProjectUpdateSchema(name="Renamed project")
        result = await repo.update(uuid.uuid4(), data, uuid.uuid4())

        assert result is None
        mock_session.commit.assert_not_called()


class TestDelete:

    async def test_delete(self, repo, mock_session, sample_project):
        await repo.delete(sample_project)

        mock_session.delete.assert_awaited_once_with(sample_project)
        mock_session.commit.assert_awaited_once()


class TestSaveMembersWithPermission:

    async def test_save_members_with_permission(self, repo, mock_session, sample_project):
        member = ProjectMember(
            project_id=sample_project.id, user_id=uuid.uuid4(), permission=ProjectPermission.READ
        )

        result = await repo.save_members_with_permission(member)

        mock_session.add.assert_called_once_with(member)
        mock_session.commit.assert_awaited_once()
        mock_session.refresh.assert_awaited_once_with(member, attribute_names=["user"])
        assert result == member


class TestGetUserPermission:

    async def test_get_user_permission_found(self, repo, mock_session):
        exec_result = MagicMock()
        exec_result.scalar_one_or_none.return_value = ProjectPermission.WRITE
        mock_session.execute.return_value = exec_result

        result = await repo.get_user_permission(uuid.uuid4(), uuid.uuid4())

        assert result == ProjectPermission.WRITE

    async def test_get_user_permission_not_found(self, repo, mock_session):
        exec_result = MagicMock()
        exec_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = exec_result

        result = await repo.get_user_permission(uuid.uuid4(), uuid.uuid4())

        assert result is None

