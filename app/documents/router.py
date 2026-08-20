import uuid

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, status, UploadFile, File
from typing import Annotated
from app.documents.interfaces.service import IDocumentService
from app.shared.dependencies import get_current_user
from app.users.models import User


document_router = APIRouter(prefix="/document", tags=["documents"], route_class=DishkaRoute)


@document_router.get("/{document_id}", status_code=status.HTTP_200_OK)
async def get_document(document_id: uuid.UUID,
                       current_user: Annotated[User, Depends(get_current_user)],
                       document_service: FromDishka[IDocumentService],
                       is_resized: bool = False,
                       ):

    return await document_service.download_document(document_id, current_user.id, is_resized)



@document_router.put("/{document_id}", status_code=status.HTTP_202_ACCEPTED)
async def update_document(document_id: uuid.UUID,
                          current_user: Annotated[User, Depends(get_current_user)],
                          document_service: FromDishka[IDocumentService],
                          file: UploadFile = File(...)):

    return await document_service.update_document(file, document_id, current_user.id)


@document_router.delete("/{document_id}", status_code=status.HTTP_202_ACCEPTED)
async def delete_document(document_id: uuid.UUID,
                          current_user: Annotated[User, Depends(get_current_user)],
                          document_service: FromDishka[IDocumentService]):
    return await document_service.delete_document(document_id, current_user.id)




# @document_router.post('/files/upload-url', response_model=UploadUrlResponse, status_code=status.HTTP_202_ACCEPTED)
# @inject
# async def get_upload_url(data: UploadUrlRequest, s3_service: S3Service = Depends(Provide[Container.s3_service])):
#     try:
#         result = await s3_service.generate_upload_url(file_name=data.file_name, content_type=data.content_type)
#         return result
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Cannot generate presigned url: {str(e)}"
#         )
#
# @document_router.get('/files/download/{file_key:path}', status_code=status.HTTP_200_OK)
# @inject
# async def download_file(file_key: str,
#                         s3_service: S3Service = Depends(Provide[Container.s3_service])):
#     try:
#         url = await s3_service.get_download_url(file_key=file_key)
#         return {"download_url": url}
#     except Exception as e:
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
