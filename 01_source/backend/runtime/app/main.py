# 01_source/backend/runtime/app/main.py
# 02/04/2026

from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.db import init_db  # 🔥 IMPORTANTE
from app.routers.health import router as health_router
from app.routers.internal_runtime import router as internal_runtime_router
from app.routers.allocations import router as allocations_router
from app.routers.locker_state import router as locker_state_router
from app.routers.hardware import router as hardware_router
from app.routers.catalog import router as catalog_router
from app.routers.dev_catalog import router as dev_catalog_router
from app.services.runtime_bootstrap_service import safe_bootstrap_runtime_on_startup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backend_runtime")


app = FastAPI(
    title="ELLAN Backend Operacional Canônico - runtime operacional multi-locker",
    version="1.0.3",
)


@app.on_event("startup")
def startup():
    logger.info("runtime_startup_begin")

    # =========================================================
    # 🔥 NOVO — INIT SQLITE OPERACIONAL
    # =========================================================
    try:
        init_db()
        logger.info("runtime_sqlite_init_ok")
    except Exception:
        logger.exception("runtime_sqlite_init_failed")
        if settings.runtime_fail_fast_on_startup_error:
            raise

    # =========================================================
    # Bootstrap central (Postgres)
    # =========================================================
    try:
        result = safe_bootstrap_runtime_on_startup()
        logger.info("runtime_startup_bootstrap_ok extra=%s", result)
    except HTTPException as exc:
        logger.exception("runtime_startup_bootstrap_failed")

        if settings.runtime_fail_fast_on_startup_error:
            raise

        logger.error(
            "runtime_startup_bootstrap_failed_but_service_continues detail=%s",
            exc.detail,
        )
    except Exception:
        logger.exception("runtime_startup_unexpected_failure")
        if settings.runtime_fail_fast_on_startup_error:
            raise


app.include_router(health_router)
app.include_router(internal_runtime_router)
app.include_router(allocations_router)
app.include_router(locker_state_router)
app.include_router(hardware_router)
app.include_router(catalog_router)
app.include_router(dev_catalog_router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail if isinstance(exc.detail, dict) else {
            "type": "HTTP_EXCEPTION",
            "message": str(exc.detail),
            "retryable": False,
            "path": str(request.url.path),
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "type": "UNHANDLED_EXCEPTION",
            "message": str(exc),
            "retryable": True,
            "service": "backend_runtime",
            "path": str(request.url.path),
        },
    )