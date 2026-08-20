import uuid
from abc import ABC, abstractmethod

class IDocumentService(ABC):
    @abstractmethod
    async def upload_document(self, file, project_id: uuid.UUID, current_user_id: uuid.UUID):
        pass

    @abstractmethod
    async def get_all_project_documents(self, project_id: uuid.UUID, current_user_id: uuid.UUID):
        pass

    @abstractmethod
    async def download_document(self, document_id: uuid.UUID, current_user_id: uuid.UUID, is_resized: bool = False):
        pass

    @abstractmethod
    async def update_document(self, new_file,document_id: uuid.UUID, current_user_id: uuid.UUID):
        pass

    @abstractmethod
    async def delete_document(self, document_id: uuid.UUID, current_user_id: uuid.UUID):
        pass


class IS3Service(ABC):
    @abstractmethod
    async def generate_upload_url(self, file_name: str, content_type: str) -> str:
        pass

    @abstractmethod
    async def get_download_url(
        self,
        file_key: str,
        file_name: str | None = None,
        content_type: str | None = None,
        expires_in: int = 3600,
    ) -> str:
        pass
