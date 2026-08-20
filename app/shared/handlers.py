from fastapi import Request
from fastapi.responses import JSONResponse

from app.shared.exceptions import BaseAppException


def base_app_exception_handler(
    request: Request, exception: BaseAppException
) -> JSONResponse:
    return JSONResponse(
        status_code=exception.status_code, content={"detail": exception.message}
    )
