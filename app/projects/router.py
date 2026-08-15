import uuid

from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, Depends, status, UploadFile, File, Query
from typing import List
from typing import Annotated
from app.documents.interfaces.service import IDocumentService
from app.projects.interfaces.service import IProjectService
from app.projects.schemas import (ProjectCreateSchema, ProjectsListSchema,
                                  ProjectDetailsSchema, ProjectUpdateSchema,
                                  ProjectCreatedSchema, DocumentsListSchema, InviteMemberResponse)
from app.shared.container import Container
from app.shared.dependencies import get_current_user
from app.users.models import User
from app.projects.models import Project, ProjectPermission


projects_router = APIRouter(prefix="/projects", tags=["projects"])
project_router = APIRouter(prefix="/project", tags=["project"])




@projects_router.post("/", response_model=ProjectCreatedSchema, status_code=status.HTTP_201_CREATED)
@inject
async def create_project(project_data: ProjectCreateSchema,
                         current_user: Annotated[User, Depends(get_current_user)],
                         project_service: Annotated[IProjectService, Depends(Provide[Container.project_service])]):

    project = Project(**project_data.model_dump(), owner_id=current_user.id)
    return await project_service.create_project(project, current_user.id)




@projects_router.get("/", response_model=list[ProjectsListSchema], status_code=status.HTTP_200_OK)
@inject
async def get_projects(current_user: Annotated[User, Depends(get_current_user)],
                       project_service: Annotated[IProjectService, Depends(Provide[Container.project_service])]):
    return await project_service.get_projects_with_access(current_user.id)



@project_router.get("/{project_id}/info", response_model=ProjectDetailsSchema, status_code=status.HTTP_200_OK)
@inject
async def get_project_details(project_id: uuid.UUID, current_user: Annotated[User,Depends(get_current_user)],
                              project_service: Annotated[IProjectService, Depends(Provide[Container.project_service])]):
    return await project_service.get_project_details(project_id, current_user.id)



@project_router.put("/{project_id}/info", response_model=ProjectDetailsSchema, status_code=status.HTTP_202_ACCEPTED)
@inject
async def update_project_details(project_id: uuid.UUID,
                                 project_data : ProjectUpdateSchema,
                                 current_user: Annotated[User, Depends(get_current_user)],
                                 project_service: Annotated[IProjectService, Depends(Provide[Container.project_service])]):
    return await project_service.update_project_details(project_id, project_data, current_user.id)



@project_router.delete("/{project_id}", status_code=status.HTTP_202_ACCEPTED)
@inject
async def delete_project(project_id: uuid.UUID,
                         current_user: Annotated[User, Depends(get_current_user)],
                         project_service: Annotated[IProjectService, Depends(Provide[Container.project_service])]):
    return await project_service.delete_project(project_id, current_user.id)



@project_router.post("/{project_id}/invite", response_model=InviteMemberResponse, status_code=status.HTTP_202_ACCEPTED)
@inject
async def invite_member(project_id: uuid.UUID,
                        user: Annotated[str, Query(description="User to invite")],
                        permission: Annotated[ProjectPermission, Query(
                        description="Permission for the invited user",)],
                        current_user: Annotated[User, Depends(get_current_user)],
                        project_service: Annotated[IProjectService, Depends(Provide[Container.project_service])]):

    return await project_service.invite_member(project_id, user, current_user.id, permission)



@project_router.get("/{project_id}/share", status_code=status.HTTP_200_OK)
@inject
async def share_project(project_id: uuid.UUID, email: Annotated[str, Query(description="Email to share")],
                        permission: Annotated[ProjectPermission, Query(description="Permission for the shared user",)],
                        current_user: Annotated[User, Depends(get_current_user)],
                        project_service: Annotated[IProjectService, Depends(Provide[Container.project_service])]):

    return await project_service.share_project_link(project_id, email, current_user.id, permission)


@project_router.post('/join', status_code=status.HTTP_200_OK)
@inject
async def join_project(token: Annotated[str, Query(description="Invite token")],
                       current_user: Annotated[User, Depends(get_current_user)],
                       project_service: Annotated[IProjectService, Depends(Provide[Container.project_service])]):

    return await project_service.join_project_by_token(token, current_user.id)




@project_router.post("/{project_id}/documents", response_model=dict, status_code=status.HTTP_201_CREATED)
@inject
async def create_document(project_id: uuid.UUID,
                          current_user: Annotated[User, Depends(get_current_user)],
                          document_service: Annotated[IDocumentService, Depends(Provide[Container.document_service])],
                          file: UploadFile = File(...),):
    return await document_service.upload_document(file, project_id, current_user.id)


@project_router.get("/{project_id}/documents", response_model=List[DocumentsListSchema], status_code=status.HTTP_200_OK)
@inject
async def get_documents(project_id: uuid.UUID,
                        current_user: Annotated[User, Depends(get_current_user)],
                        document_service: Annotated[IDocumentService, Depends(Provide[Container.document_service])]):
    return await document_service.get_all_project_documents(project_id, current_user.id)
