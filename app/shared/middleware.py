import logging
import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

logger = logging.getLogger('app.requests')

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = str(uuid.uuid4())
        start_time = time.perf_counter()

        response = await call_next(request)
        response_time = time.perf_counter() - start_time

        logger.info(
            "request_id=%s endpoint=%s response_time=%.3fs status_code=%s",
            request_id,
            request.url.path,
            response_time,
            response.status_code,
        )

        response.headers["X-Request-Id"] = request_id

        return response