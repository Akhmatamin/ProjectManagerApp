from app.shared.exceptions import BaseAppException

class InvalidProjectMembers(BaseAppException):
    def __init__(self, message:str = "Some members doesn't exist"):
        super().__init__(message, status_code=400)

class ProjectNotFound(BaseAppException):
    def __init__(self, message:str = "Projects not found"):
        super().__init__(message, status_code=404)

class NotMemberOrNoProject(BaseAppException):
    def __init__(self, message:str = "Project doesn't exist or not have access"):
        super().__init__(message, status_code=403)

class AccessDenied(BaseAppException):
    def __init__(self, message:str = "Access denied"):
        super().__init__(message, status_code=403)

class DocumentNotFound(BaseAppException):
    def __init__(self, message:str = "Document not found"):
        super().__init__(message, status_code=404)

class UserAlreadyMember(BaseAppException):
    def __init__(self, message:str = "User already member of the project"):
        super().__init__(message, status_code=400)

class UserNotFound(BaseAppException):
    def __init__(self, message:str = "User doesn't exist"):
        super().__init__(message, status_code=404)