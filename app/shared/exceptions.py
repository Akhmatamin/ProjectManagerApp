class BaseAppException(Exception):
    def __init__(self, message: str, status_code: int):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class InvalidToken(BaseAppException):
    def __init__(self, message: str = "Invalid token"):
        super().__init__(message, status_code=400)

class TokenExpired(BaseAppException):
    def __init__(self, message: str = "Token has expired"):
        super().__init__(message, status_code=400)

class InvalidLink(BaseAppException):
    def __init__(self, message: str = "Invalid link"):
        super().__init__(message, status_code=400)
