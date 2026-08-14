import uuid

from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, Depends, status, UploadFile, File
from fastapi.responses import FileResponse
from urllib.parse import quote
from typing import Annotated
from app.documents.interfaces.service import IDocumentService
from app.shared.container import Container
from app.shared.dependencies import get_current_user
from app.users.models import User


document_router = APIRouter(prefix="/document", tags=["documents"])


@document_router.get("/{document_id}", status_code=status.HTTP_200_OK)
@inject
async def get_document(document_id: uuid.UUID,
                       current_user: Annotated[User, Depends(get_current_user)],
                       document_service: Annotated[IDocumentService, Depends(Provide[Container.document_service])]):
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
@inject
async def update_document(document_id: uuid.UUID,
                          current_user: Annotated[User, Depends(get_current_user)],
                          document_service: Annotated[IDocumentService, Depends(Provide[Container.document_service])],
                          file: UploadFile = File(...)):

    return await document_service.update_document(file, document_id, current_user.id)


@document_router.delete("/{document_id}", status_code=status.HTTP_202_ACCEPTED)
@inject
async def delete_document(document_id: uuid.UUID,
                          current_user: Annotated[User, Depends(get_current_user)],
                          document_service: Annotated[IDocumentService, Depends(Provide[Container.document_service])]):
    return await document_service.delete_document(document_id, current_user.id)


