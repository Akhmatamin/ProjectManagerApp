import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.projects.exceptions import (
    AccessDenied,
    NotMemberOrNoProject,
    ProjectNotFound,
    UserAlreadyMember,
    UserNotFound,
)
from app.projects.models import Project, ProjectMember, ProjectPermission
from app.projects.schemas import ProjectUpdateSchema
from app.projects.service import ProjectService
from app.shared.exceptions import InvalidLink

pytestmark = pytest.mark.asyncio


@pytest.fixture
def project_repo():
    return AsyncMock()


@pytest.fixture
def user_repo():
    return AsyncMock()


@pytest.fixture
def invite_repo():
    return AsyncMock()


@pytest.fixture
def email_service():
    return AsyncMock()


@pytest.fixture
def settings():
    settings = MagicMock()
    settings.invite_link_expire_seconds = 3600
    settings.frontend_base_url = "https://app.example.com/join"
    return settings


@pytest.fixture
def service(project_repo, user_repo, invite_repo, email_service, settings):
    return ProjectService(
        project_repo=project_repo,
        user_repo=user_repo,
        invite_repo=invite_repo,
        email_service=email_service,
        settings=settings,
    )


@pytest.fixture
def owner_id():
    return uuid.uuid4()


@pytest.fixture
def sample_project(owner_id):
    project = Project(id=uuid.uuid4(),
        name="My Project",
        owner_id=owner_id,
    )
    project.user_memberships = []
    return project


@pytest.fixture
def sample_user():
    user = MagicMock()
    user.id = uuid.uuid4()
    user.email = "member@example.com"
    return user



class TestCreateProject:

    async def test_create_project_success(self, service, project_repo, user_repo, owner_id):
        user_repo.get_by_id.return_value = MagicMock(id=owner_id)
        new_project = Project(id=uuid.uuid4(), name="New project")
        new_project.user_memberships = []
        project_repo.save.return_value = new_project

        result = await service.create_project(new_project, owner_id)

        user_repo.get_by_id.assert_awaited_once_with(owner_id)
        assert len(new_project.user_memberships) == 1
        membership = new_project.user_memberships[0]
        assert membership.user_id == owner_id
        assert membership.permission == ProjectPermission.WRITE
        project_repo.save.assert_awaited_once_with(new_project)
        assert result == new_project


    async def test_create_project_user_not_found(self, service, project_repo, user_repo):
        user_repo.get_by_id.return_value = None
        new_project = Project(id=uuid.uuid4(), name="New project")
        new_project.user_memberships = []

        with pytest.raises(UserNotFound):
            await service.create_project(new_project, uuid.uuid4())

        project_repo.save.assert_not_called()



class TestGetProjectsWithAccess:

    async def test_get_projects_with_access_success(self, service, project_repo, sample_project):
        project_repo.get_by_user_id.return_value = [sample_project]

        result = await service.get_projects_with_access(uuid.uuid4())

        assert result == [sample_project]

    async def test_get_projects_with_access_empty(self, service, project_repo):
        project_repo.get_by_user_id.return_value = []

        with pytest.raises(ProjectNotFound):
            await service.get_projects_with_access(uuid.uuid4())



class TestGetProjectDetails:

    async def test_get_project_details_success(self, service, project_repo, sample_project):
        project_repo.get_if_user_member.return_value = sample_project

        result = await service.get_project_details(sample_project.id, uuid.uuid4())

        assert result == sample_project

    async def test_get_project_details_not_found(self, service, project_repo):
        project_repo.get_if_user_member.return_value = None

        with pytest.raises(ProjectNotFound):
            await service.get_project_details(uuid.uuid4(), uuid.uuid4())



class TestUpdateProjectDetails:

    async def test_update_project_details_success(self, service, project_repo, sample_project):
        project_repo.get_user_permission.return_value = ProjectPermission.WRITE
        project_repo.update.return_value = sample_project
        data = ProjectUpdateSchema(name="Renamed")

        result = await service.update_project_details(sample_project.id, data, uuid.uuid4())

        assert result == sample_project

    async def test_update_project_details_not_member_or_missing(self, service, project_repo):
        project_repo.get_user_permission.return_value = None
        data = ProjectUpdateSchema(name="Renamed")

        with pytest.raises(NotMemberOrNoProject):
            await service.update_project_details(uuid.uuid4(), data, uuid.uuid4())

        project_repo.update.assert_not_called()

    async def test_update_project_details_read_permission_forbidden(self, service, project_repo):
        project_repo.get_user_permission.return_value = ProjectPermission.READ
        data = ProjectUpdateSchema(name="Renamed")

        with pytest.raises(AccessDenied):
            await service.update_project_details(uuid.uuid4(), data, uuid.uuid4())

        project_repo.update.assert_not_called()



class TestDeleteProject:

    async def test_delete_project_success(self, service, project_repo, sample_project, owner_id):
        project_repo.get_by_id.return_value = sample_project

        result = await service.delete_project(sample_project.id, owner_id)

        project_repo.delete.assert_awaited_once_with(sample_project)
        assert result == {"message": "Project deleted successfully"}

    async def test_delete_project_not_found(self, service, project_repo):
        project_repo.get_by_id.return_value = None

        with pytest.raises(AccessDenied):
            await service.delete_project(uuid.uuid4(), uuid.uuid4())

        project_repo.delete.assert_not_called()

    async def test_delete_project_not_owner(self, service, project_repo, sample_project):
        project_repo.get_by_id.return_value = sample_project

        with pytest.raises(AccessDenied):
            await service.delete_project(sample_project.id, uuid.uuid4())

        project_repo.delete.assert_not_called()



class TestInviteMember:

    async def test_invite_member_success(self, service, project_repo, user_repo,
                                          sample_project, sample_user, owner_id):
        project_repo.get_by_id.return_value = sample_project
        user_repo.get_by_email.return_value = sample_user
        project_repo.get_user_permission.return_value = None
        saved_member = ProjectMember(
            project_id=sample_project.id, user_id=sample_user.id,
            permission=ProjectPermission.READ,
        )
        project_repo.save_members_with_permission.return_value = saved_member

        result = await service.invite_member(
            sample_project.id, sample_user.email, owner_id, ProjectPermission.READ
        )

        project_repo.save_members_with_permission.assert_awaited_once()
        assert result == {
            "message": "Member invited successfully",
            "project_id": saved_member.project_id,
        }

    async def test_invite_member_project_not_found(self, service, project_repo):
        project_repo.get_by_id.return_value = None

        with pytest.raises(ProjectNotFound):
            await service.invite_member(uuid.uuid4(), "a@test.com", uuid.uuid4(), ProjectPermission.READ)

    async def test_invite_member_not_owner(self, service, project_repo, sample_project):
        project_repo.get_by_id.return_value = sample_project

        with pytest.raises(AccessDenied):
            await service.invite_member(
                sample_project.id, "a@test.com", uuid.uuid4(), ProjectPermission.READ
            )

    async def test_invite_member_user_not_found(self, service, project_repo, user_repo,
                                                  sample_project, owner_id):
        project_repo.get_by_id.return_value = sample_project
        user_repo.get_by_email.return_value = None

        with pytest.raises(UserNotFound):
            await service.invite_member(
                sample_project.id, "test@test.com", owner_id, ProjectPermission.READ
            )

    async def test_invite_member_already_member(self, service, project_repo, user_repo,
                                                 sample_project, sample_user, owner_id):
        project_repo.get_by_id.return_value = sample_project
        user_repo.get_by_email.return_value = sample_user
        project_repo.get_user_permission.return_value = ProjectPermission.READ

        with pytest.raises(UserAlreadyMember):
            await service.invite_member(
                sample_project.id, sample_user.email, owner_id, ProjectPermission.WRITE
            )

        project_repo.save_members_with_permission.assert_not_called()



class TestShareProjectLink:

    async def test_share_project_link_success(self, service, project_repo, invite_repo,
                                                email_service, settings, sample_project, owner_id):
        project_repo.get_by_id.return_value = sample_project

        with patch("app.projects.service.create_invite_token", return_value="signed-token") as mock_create, \
             patch("app.projects.service.uuid.uuid4", return_value=uuid.UUID(int=1)):
            result = await service.share_project_link(
                sample_project.id, "invite@test.com", owner_id, ProjectPermission.READ
            )

        mock_create.assert_called_once()
        invite_repo.save_invite_jti.assert_awaited_once()
        call_kwargs = invite_repo.save_invite_jti.call_args.kwargs
        assert call_kwargs["payload"]["email"] == "invite@test.com"
        assert call_kwargs["payload"]["project_id"] == str(sample_project.id)
        assert call_kwargs["ttl_seconds"] == settings.invite_link_expire_seconds

        email_service.send_project_invite.assert_awaited_once()
        email_kwargs = email_service.send_project_invite.call_args.kwargs
        assert email_kwargs["email"] == "invite@test.com"
        assert email_kwargs["project_name"] == sample_project.name
        assert "signed-token" in email_kwargs["join_link"]

        assert result == {"message": "Email for invite sent to user: invite@test.com"}

    async def test_share_project_link_project_not_found(self, service, project_repo):
        project_repo.get_by_id.return_value = None

        with pytest.raises(ProjectNotFound):
            await service.share_project_link(
                uuid.uuid4(), "a@test.com", uuid.uuid4(), ProjectPermission.READ
            )

    async def test_share_project_link_not_owner(self, service, project_repo, sample_project):
        project_repo.get_by_id.return_value = sample_project

        with pytest.raises(AccessDenied):
            await service.share_project_link(
                sample_project.id, "b@test.com", uuid.uuid4(), ProjectPermission.READ
            )



class TestJoinProjectByToken:

    def _decoded_payload(self, project_id, permission=ProjectPermission.READ, jti="jti-1"):
        return {
            "project_id": str(project_id),
            "permission": permission.value,
            "jti": jti,
        }

    async def test_join_project_by_token_success(self, service, project_repo, user_repo, invite_repo,
                                                   sample_project, sample_user):
        payload = self._decoded_payload(sample_project.id)
        invite_data = {"email": sample_user.email, "project_id": str(sample_project.id),
                       "permission": ProjectPermission.READ.value}
        invite_repo.get_invite_jti.return_value = invite_data
        project_repo.get_by_id.return_value = sample_project
        user_repo.get_by_id.return_value = sample_user
        project_repo.get_user_permission.return_value = None
        saved_member = ProjectMember(
            project_id=sample_project.id, user_id=sample_user.id,
            permission=ProjectPermission.READ,
        )
        project_repo.save_members_with_permission.return_value = saved_member

        with patch("app.projects.service.decode_invite_token", return_value=payload):
            result = await service.join_project_by_token("token-value", sample_user.id)

        invite_repo.delete_invite_jti.assert_awaited_once_with(jti="jti-1")
        assert result == {
            "message": "You have successfully joined to project",
            "project_id": saved_member.project_id,
        }

    async def test_join_project_by_token_invalid_link(self, service, invite_repo, sample_project):
        payload = self._decoded_payload(sample_project.id)
        invite_repo.get_invite_jti.return_value = None

        with(
            patch("app.projects.service.decode_invite_token", return_value=payload),
            pytest.raises(InvalidLink)
        ):
            await service.join_project_by_token("token-value", uuid.uuid4())

    async def test_join_project_by_token_project_not_found(self, service, project_repo, invite_repo,
                                                             sample_project):
        payload = self._decoded_payload(sample_project.id)
        invite_repo.get_invite_jti.return_value = {"email": None}
        project_repo.get_by_id.return_value = None

        with(
            patch("app.projects.service.decode_invite_token", return_value=payload),
            pytest.raises(ProjectNotFound)
        ):
            await service.join_project_by_token("token-value", uuid.uuid4())

    async def test_join_project_by_token_user_not_found(self, service, project_repo, user_repo,
                                                          invite_repo, sample_project):
        payload = self._decoded_payload(sample_project.id)
        invite_repo.get_invite_jti.return_value = {"email": None}
        project_repo.get_by_id.return_value = sample_project
        user_repo.get_by_id.return_value = None

        with(
            patch("app.projects.service.decode_invite_token", return_value=payload),
            pytest.raises(UserNotFound)
        ):
            await service.join_project_by_token("token-value", uuid.uuid4())

    async def test_join_project_by_token_email_mismatch(self, service, project_repo, user_repo,
                                                          invite_repo, sample_project, sample_user):
        payload = self._decoded_payload(sample_project.id)
        invite_repo.get_invite_jti.return_value = {"email": "someone@test.com"}
        project_repo.get_by_id.return_value = sample_project
        user_repo.get_by_id.return_value = sample_user

        with(
            patch("app.projects.service.decode_invite_token", return_value=payload),
            pytest.raises(AccessDenied)
        ):
            await service.join_project_by_token("token-value", sample_user.id)

    async def test_join_project_by_token_already_member(self, service, project_repo, user_repo,
                                                          invite_repo, sample_project, sample_user):
        payload = self._decoded_payload(sample_project.id)
        invite_repo.get_invite_jti.return_value = {"email": sample_user.email}
        project_repo.get_by_id.return_value = sample_project
        user_repo.get_by_id.return_value = sample_user
        project_repo.get_user_permission.return_value = ProjectPermission.READ

        with(
            patch("app.projects.service.decode_invite_token", return_value=payload),
            pytest.raises(UserAlreadyMember)
        ):
            await service.join_project_by_token("token-value", sample_user.id)

        project_repo.save_members_with_permission.assert_not_called()