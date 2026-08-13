import uuid

from fastapi import APIRouter, Depends, status, UploadFile, File
from fastapi.responses import FileResponse
from urllib.parse import quote
from typing import List
from app.projects.interfaces.service import IProjectService, IDocumentService
from app.projects.schemas import (ProjectCreateSchema, ProjectsListSchema,
                                  ProjectDetailsSchema, ProjectUpdateSchema,
                                  ProjectCreatedSchema, DocumentsListSchema, InviteMemberResponse)

from app.shared.dependencies import get_current_user, get_project_service, get_document_service
from app.users.models import User
from app.projects.models import Project


projects_router = APIRouter(prefix="/projects", tags=["projects"])
project_router = APIRouter(prefix="/project", tags=["project"])
document_router = APIRouter(prefix="/document", tags=["documents"])

@projects_router.post("/", response_model=ProjectCreatedSchema, status_code=status.HTTP_201_CREATED)
async def create_project(project_data: ProjectCreateSchema,
                         current_user: User = Depends(get_current_user),
                         project_service: IProjectService = Depends(get_project_service)):

    project = Project(**project_data.model_dump(), owner_id=current_user.id)
    return await project_service.create_project(project, current_user.id)



@projects_router.get("/", response_model=list[ProjectsListSchema], status_code=status.HTTP_200_OK)
async def get_projects(current_user: User = Depends(get_current_user),
                       project_service: IProjectService = Depends(get_project_service)):
    return await project_service.get_projects_with_access(current_user.id)

@project_router.get("/{project_id}/info", response_model=ProjectDetailsSchema, status_code=status.HTTP_200_OK)
async def get_project_details(project_id: uuid.UUID, current_user: User = Depends(get_current_user),
                              project_service: IProjectService = Depends(get_project_service)):
    return await project_service.get_project_details(project_id, current_user.id)

@project_router.put("/{project_id}/info", response_model=ProjectDetailsSchema, status_code=status.HTTP_202_ACCEPTED)
async def update_project_details(project_id: uuid.UUID,
                                 project_data : ProjectUpdateSchema,
                                 current_user: User = Depends(get_current_user),
                                 project_service: IProjectService = Depends(get_project_service)):
    return await project_service.update_project_details(project_id, project_data, current_user.id)

@project_router.delete("/{project_id}", status_code=status.HTTP_202_ACCEPTED)
async def delete_project(project_id: uuid.UUID,
                         current_user: User = Depends(get_current_user),
                         project_service: IProjectService = Depends(get_project_service)):
    return await project_service.delete_project(project_id, current_user.id)


@project_router.post("/{project_id}/invite", response_model=InviteMemberResponse, status_code=status.HTTP_202_ACCEPTED)
async def invite_member(project_id: uuid.UUID,
                        user: str,
                        current_user: User = Depends(get_current_user),
                        project_service: IProjectService = Depends(get_project_service)):

    return await project_service.invite_member(project_id, user, current_user.id)


@project_router.post("/{project_id}/documents", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_document(project_id: uuid.UUID,
                          file: UploadFile = File(...),
                          current_user: User = Depends(get_current_user),
                          document_service: IDocumentService = Depends(get_document_service)):
    return await document_service.upload_document(file, project_id, current_user.id)


@project_router.get("/{project_id}/documents", response_model=List[DocumentsListSchema], status_code=status.HTTP_200_OK)
async def get_documents(project_id: uuid.UUID,
                        current_user: User = Depends(get_current_user),
                        document_service: IDocumentService = Depends(get_document_service)):
    return await document_service.get_all_project_documents(project_id, current_user.id)


@document_router.get("/{document_id}", status_code=status.HTTP_200_OK)
async def get_document(document_id: uuid.UUID,
                       current_user: User = Depends(get_current_user),
                       document_service: IDocumentService = Depends(get_document_service)):
    file_object = await document_service.download_document(document_id, current_user.id)
    encoded_filename = quote(file_object.filename)
    full_path = f"./uploaded_files/{file_object.path}"  # Temporary solution, will be changed to S3 url etc.

    return FileResponse(
        path=full_path,
        media_type=file_object.content_type,
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
        }
    )

@document_router.put("/{document_id}", status_code=status.HTTP_202_ACCEPTED)
async def update_document(document_id: uuid.UUID,
                          current_user: User = Depends(get_current_user),
                          file: UploadFile = File(...),
                          document_service: IDocumentService = Depends(get_document_service)):

    return await document_service.update_document(file, document_id, current_user.id)

@document_router.delete("/{document_id}", status_code=status.HTTP_202_ACCEPTED)
async def delete_document(document_id: uuid.UUID,
                          current_user: User = Depends(get_current_user),
                          document_service: IDocumentService = Depends(get_document_service)):
    return await document_service.delete_document(document_id, current_user.id)


