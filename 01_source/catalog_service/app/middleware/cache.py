from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class CacheStatusMiddleware(BaseHTTPMiddleware):
    """Propaga X-Cache quando `request.state.catalog_cache_status` for definido."""

    async def dispatch(self, request: Request, call_next):
        request.state.catalog_cache_status = None
        response = await call_next(request)
        st = getattr(request.state, "catalog_cache_status", None)
        if st:
            response.headers["X-Cache"] = st
        return response
