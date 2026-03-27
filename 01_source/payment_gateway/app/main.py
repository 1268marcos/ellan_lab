# 01_source/payment_gateway/app/main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import traceback
import time

from app.models.gateway_response_model import HealthResponse
from app.routers.payment import router as payment_router
from app.routers.audit import router as audit_router
from app.routers.risk import router as risk_router
from app.routers.audit_log import router as audit_log_router
from app.routers.audit_snapshot import router as audit_snapshot_router
from app.routers.lockers import router as lockers_router


app = FastAPI(
    title="ELLAN Payment Gateway (01_source/payment_gateway/app/main.py)",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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


@app.get("/health", response_model=HealthResponse)
async def health():
    return {
        "status": "gateway_ok",
        "service": "payment_gateway",
        "version": "1.0.0",
    }


# Transforme o 500 em JSON (handler global)
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "service": "payment_gateway",
            "result": "error",
            "error": {
                "type": exc.__class__.__name__,
                "message": str(exc),
                "retryable": True,
            },
            "severity": "HIGH",
            "severity_code": "GATEWAY_UNHANDLED_EXCEPTION",
            "timestamp": time.time(),
            # em prod você removeria stacktrace; em lab ajuda muito:
            "debug": {
                "path": str(request.url.path),
                "traceback": traceback.format_exc().splitlines()[-30:],
            },
        },
    )