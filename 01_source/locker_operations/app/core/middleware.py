from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from shared_kernel.observability.correlation_id import set_correlation_id
from shared_kernel.observability.request_id import set_request_id


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        set_request_id(request.headers.get("X-Request-Id"))
        set_correlation_id(request.headers.get("X-Correlation-Id"))
        response = await call_next(request)
        return response
