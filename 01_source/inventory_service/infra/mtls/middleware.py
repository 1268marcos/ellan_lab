from __future__ import annotations

import os
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class MTLSMiddleware(BaseHTTPMiddleware):
    """When MTLS_ENFORCE=1, requires X-mTLS-Subject (simulates mesh-terminated mTLS)."""

    def __init__(self, app, ca_file: str | None = None) -> None:
        super().__init__(app)
        self.ca_file = ca_file or os.getenv("MTLS_CA_FILE", "")
        self.enforce = os.getenv("MTLS_ENFORCE", "0") == "1"

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        if not self.enforce:
            return await call_next(request)
        subj = request.headers.get("X-mTLS-Subject") or request.headers.get("X-Forwarded-Client-Cert-Subject")
        if not subj:
            return JSONResponse({"detail": "mTLS required"}, status_code=403)
        return await call_next(request)


def maybe_add_mtls(app, ca_file: str | None = None) -> None:
    if os.getenv("MTLS_ENFORCE", "0") == "1":
        app.add_middleware(MTLSMiddleware, ca_file=ca_file)
