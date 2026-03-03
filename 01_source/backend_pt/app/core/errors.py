# 01_source/backend_pt/app/core/errors.py
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import traceback, os

SERVICE_NAME = os.getenv("SERVICE_NAME", "backend_pt")

def rich_error_payload(request: Request, *, status_code: int, err_type: str, message: str, retryable: bool, extra: dict | None = None):
    payload = {
        "ok": False,
        "service": SERVICE_NAME,
        "endpoint": request.url.path,
        "method": request.method,
        "error": {
            "type": err_type,
            "message": message,
            "retryable": retryable,
        },
    }
    if extra:
        payload["error"].update(extra)
    return payload

async def http_exception_handler(request: Request, exc: HTTPException):
    # se detail já é dict, preserva como error
    if isinstance(exc.detail, dict):
        payload = {"ok": False, "service": SERVICE_NAME, "endpoint": request.url.path, "method": request.method, "error": exc.detail}
        return JSONResponse(status_code=exc.status_code, content=payload)

    payload = rich_error_payload(
        request,
        status_code=exc.status_code,
        err_type="HTTP_ERROR",
        message=str(exc.detail),
        retryable=(exc.status_code >= 500),
    )
    return JSONResponse(status_code=exc.status_code, content=payload)

async def unhandled_exception_handler(request: Request, exc: Exception):
    debug = os.getenv("DEBUG_ERRORS", "false").lower() == "true"
    extra = {}
    if debug:
        extra["trace"] = traceback.format_exc(limit=6)
    payload = rich_error_payload(
        request,
        status_code=500,
        err_type="INTERNAL_ERROR",
        message=str(exc),
        retryable=True,
        extra=extra,
    )
    return JSONResponse(status_code=500, content=payload)