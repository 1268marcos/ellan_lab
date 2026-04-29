# 01_source/backend/billing_fiscal_service/app/main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import time
import uuid
import logging

from app.api.routes_admin_fiscal import router as admin_fiscal_router
from app.api.routes_fiscal import router as fiscal_router
from app.api.routes_invoice import router as invoice_router
from app.api.routes_partner_billing import router as partner_billing_router
from app.core.db import init_db
from app.core.config import settings

app = FastAPI(title="Billing Fiscal Service")
logger = logging.getLogger("billing_fiscal_service")


def _is_dev_env() -> bool:
    return str(settings.app_env or "dev").strip().lower() in {"dev", "development", "local", "test"}


def _resolve_cors_origins() -> list[str]:
    raw = str(os.getenv("CORS_ALLOW_ORIGINS", "")).strip()
    if raw:
        return [item.strip() for item in raw.split(",") if item.strip()]
    if _is_dev_env():
        return ["http://localhost:5173", "http://localhost:3000"]
    return []

app.add_middleware(
    CORSMiddleware,
    allow_origins=_resolve_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    if not _is_dev_env() and str(settings.internal_token or "").strip() == "dev-internal-token":
        raise RuntimeError("INTERNAL_TOKEN default não permitido fora de dev/local.")
    init_db()


app.include_router(invoice_router)
app.include_router(fiscal_router)
app.include_router(admin_fiscal_router)
app.include_router(partner_billing_router)


@app.get("/health")
def health():
    return {"status": "ok"}


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
            "service": "billing_fiscal_service",
            "result": "error",
            "error": {
                "type": exc.__class__.__name__,
                "message": "Internal server error",
            },
            "severity": "HIGH",
            "severity_code": "BILLING_UNHANDLED_EXCEPTION",
            "timestamp": time.time(),
            "trace_id": trace_id,
        },
        headers={"X-Trace-Id": trace_id},
    )