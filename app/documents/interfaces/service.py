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
    async def download_document(self, document_id: uuid.UUID, current_user_id: uuid.UUID):
        pass

    @abstractmethod
    async def update_document(self, new_file,document_id: uuid.UUID, current_user_id: uuid.UUID):
        pass

    @abstractmethod
    async def delete_document(self, document_id: uuid.UUID, current_user_id: uuid.UUID):
        pass