# 01_source/payment_gateway/app/main.py
# 12/04/2026 - uso de datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import uuid
import logging
import os
from datetime import datetime

from app.models.gateway_response_model import HealthResponse
from app.routers.payment import router as payment_router
from app.routers.audit import router as audit_router
from app.routers.risk import router as risk_router
from app.routers.audit_log import router as audit_log_router
from app.routers.audit_snapshot import router as audit_snapshot_router
from app.routers.lockers import router as lockers_router

from app.core.datetime_utils import to_iso_utc



app = FastAPI(
    title="ELLAN Payment Gateway (01_source/payment_gateway/app/main.py)",
    version="1.0.1",
)
logger = logging.getLogger("payment_gateway")


def _resolve_cors_origins() -> list[str]:
    raw = str(os.getenv("CORS_ALLOW_ORIGINS", "")).strip()
    if raw:
        return [item.strip() for item in raw.split(",") if item.strip()]
    env = str(os.getenv("APP_ENV", os.getenv("NODE_ENV", "dev"))).strip().lower()
    if env in {"dev", "development", "local", "test"}:
        return ["http://localhost:5173", "http://localhost:3000"]
    return []

app.add_middleware(
    CORSMiddleware,
    allow_origins=_resolve_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers principais
app.include_router(payment_router, tags=["gateway"])
app.include_router(lockers_router, tags=["lockers"])
app.include_router(audit_router, tags=["audit"])
app.include_router(risk_router, tags=["risk"])
app.include_router(audit_log_router, tags=["audit-log"])
app.include_router(audit_snapshot_router, tags=["audit-snapshot"])


@app.middleware("http")
async def trace_middleware(request: Request, call_next):
    trace_id = request.headers.get("X-Trace-Id") or str(uuid.uuid4())
    request.state.trace_id = trace_id
    response = await call_next(request)
    response.headers["X-Trace-Id"] = trace_id
    return response


@app.get("/health", response_model=HealthResponse)
async def health():
    return {
        "status": "gateway_ok",
        "service": "payment_gateway",
        "version": "1.0.1",
        "timestamp": datetime.utcnow().isoformat(),  # Adicionar timestamp
    }


# Rota raiz para teste básico
@app.get("/")
async def root():
    return {
        "service": "payment_gateway",
        "status": "running",
        "version": "1.0.1"
    }


# Transforme o 500 em JSON (handler global)
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
            "service": "payment_gateway",
            "result": "error",
            "error": {
                "type": exc.__class__.__name__,
                "message": "Internal server error",
                "retryable": True,
            },
            "severity": "HIGH",
            "severity_code": "GATEWAY_UNHANDLED_EXCEPTION",
            "timestamp": time.time(),
            "trace_id": trace_id,
        },
        headers={"X-Trace-Id": trace_id},
    )

