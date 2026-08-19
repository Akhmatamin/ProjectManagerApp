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


class UserAlreadyMember(BaseAppException):
    def __init__(self, message:str = "User already member of the project"):
        super().__init__(message, status_code=400)

class UserNotFound(BaseAppException):
    def __init__(self, message:str = "User doesn't exist"):
        super().__init__(message, status_code=404)

class FileKeyMissing(BaseAppException):
    def __init__(self, message:str = "File key missing"):
        super().__init__(message, status_code=400)

class NotImplementedYet(BaseAppException):
    def __init__(self, message:str = "Not all emails are available yet"):
        super().__init__(message, status_code=501)