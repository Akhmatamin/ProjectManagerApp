from app.shared.exceptions import BaseAppException


class EmailAlreadyExists(BaseAppException):
    def __init__(self, message: str = "Email already exists."):
        super().__init__(message, status_code=400)

class UserAlreadyExists(BaseAppException):
    def __init__(self, message: str = 'User already exists.'):
        super().__init__(message, status_code=400)

class InvalidCredentials(BaseAppException):
    def __init__(self, message: str = "Invalid email or password."):
        super().__init__(message, status_code=401)

class InvalidRefreshToken(BaseAppException):
    def __init__(self, message: str = "Invalid refresh token"):
        super().__init__(message, status_code=404)

class ExpiredRefreshToken(BaseAppException):
    def __init__(self, message: str = "Refresh token expired or invalid."):
        super().__init__(message, status_code=401)

class InvalidPassword(BaseAppException):
    def __init__(self, message: str = "Invalid password."):
        super().__init__(message, status_code=400)

class InvalidResetCode(BaseAppException):
    def __init__(self, message: str = "Invalid reset code."):
        super().__init__(message, status_code=400)

class InvalidEmail(BaseAppException):
    def __init__(self, message: str = "Invalid email."):
        super().__init__(message, status_code=400)