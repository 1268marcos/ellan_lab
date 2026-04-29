# 01_source/backend/order_lifecycle_service/app/main.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from fastapi.middleware.cors import CORSMiddleware
import os
import time
import uuid
import logging

from app.core.config import settings
from app.core.db import init_db
from app.core.logging import configure_logging
from app.routers.health import router as health_router
from app.routers.internal import router as internal_router

from app.api.routes_domain_events import router as domain_events_router

configure_logging()

app = FastAPI(
    title="order_lifecycle_service",
    version="0.1.0",
)
logger = logging.getLogger("order_lifecycle_service")


def _is_dev_env() -> bool:
    return str(settings.app_env or "dev").strip().lower() in {"dev", "development", "local", "test"}


def _resolve_cors_origins() -> list[str]:
    raw = str(os.getenv("CORS_ALLOW_ORIGINS", "")).strip()
    if raw:
        return [item.strip() for item in raw.split(",") if item.strip()]
    if _is_dev_env():
        return ["http://localhost:5173", "http://localhost:3000"]
    return []


@app.on_event("startup")
def on_startup() -> None:
    if not _is_dev_env() and str(settings.internal_token or "").strip() == "dev-internal-token":
        raise RuntimeError("INTERNAL_TOKEN default não permitido fora de dev/local.")
    init_db()


app.include_router(health_router)
app.include_router(internal_router)
app.include_router(domain_events_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_resolve_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "service": settings.service_name,
        "status": "ok",
        "environment": settings.app_env,
    }


@app.middleware("http")
async def trace_middleware(request: Request, call_next):
    trace_id = request.headers.get("X-Trace-Id") or str(uuid.uuid4())
    request.state.trace_id = trace_id
    response = await call_next(request)
    response.headers["X-Trace-Id"] = trace_id
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    trace_id = getattr(request.state, "trace_id", None) or str(uuid.uuid4())
    logger.exception(
        "unhandled_exception path=%s trace_id=%s error_type=%s",
        str(request.url.path),
        trace_id,
        exc.__class__.__name__,
    )
    return JSONResponse(
        status_code=500,
        content={
            "service": "order_lifecycle_service",
            "result": "error",
            "error": {
                "type": exc.__class__.__name__,
                "message": "Internal server error",
            },
            "severity": "HIGH",
            "severity_code": "LIFECYCLE_UNHANDLED_EXCEPTION",
            "timestamp": time.time(),
            "trace_id": trace_id,
        },
        headers={"X-Trace-Id": trace_id},
    )