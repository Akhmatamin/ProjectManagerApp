from app.shared.exceptions import BaseAppException


class DocumentNotFound(BaseAppException):
    def __init__(self, message:str = "Document not found"):
        super().__init__(message, status_code=404)
