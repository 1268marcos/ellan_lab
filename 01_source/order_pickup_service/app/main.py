# 01_source/order_pickup_service/app/main.py
import asyncio
import logging
import os
import time
import uuid
from collections import defaultdict, deque
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.authorization_policy import AUTHORIZATION_POLICY_MD
from app.core.config import settings
from app.core.db import SessionLocal, init_db
from app.core.version import get_version
from app.health.health import router as health_router
from app.health.internal import router as internal_health_router
from app.jobs.expiry import run_expiry_once
from app.jobs.integration_order_events_outbox import run_integration_order_events_outbox_once
from app.jobs.inventory_reserved_reconciliation import run_inventory_reserved_reconciliation_once
from app.jobs.inventory_reservations_expiry import run_inventory_reservations_expiry_once
from app.jobs.lifecycle_events_consumer import run_lifecycle_events_consumer_once
from app.jobs.reconciliation_retry import run_reconciliation_retry_once
from app.routers import (
    dev_admin,
    dev_base_catalog,
    integration_ops,
    internal,
    inventory,
    kiosk,
    logistics,
    orders,
    partners,
    pickup,
    pricing_fiscal,
    products,
)

from app.routers.public_auth import router as public_auth_router
from app.routers.public_catalog import router as public_catalog_router
from app.routers.public_me import router as public_me_router
from app.routers.public_orders import router as public_orders_router
from app.routers.public_pickup import router as public_pickup_router
from app.routers.public_fiscal import router as public_fiscal_router

from app.routers.payment_capabilities import router as payment_capabilities_router


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("order_pickup_service")
_dev_error_events: deque[dict] = deque(maxlen=300)


def _is_dev_env() -> bool:
    return str(settings.app_env or settings.node_env or "dev").strip().lower() in {"dev", "development", "local", "test"}


def _resolve_cors_origins() -> list[str]:
    raw = str(os.getenv("CORS_ALLOW_ORIGINS", "")).strip()
    if raw:
        return [item.strip() for item in raw.split(",") if item.strip()]
    if _is_dev_env():
        return ["http://localhost:5173", "http://localhost:3000"]
    return []


def _record_dev_error_event(*, level: str, status_code: int, path: str, method: str, trace_id: str, error_type: str | None = None, message: str | None = None) -> None:
    if not _is_dev_env():
        return
    _dev_error_events.appendleft(
        {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "status_code": int(status_code),
            "path": path,
            "method": method,
            "trace_id": trace_id,
            "error_type": error_type,
            "message": message,
        }
    )


class _PublicRouteRateLimiter:
    """Simple in-memory limiter for public endpoints."""

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max(1, int(max_requests))
        self.window_seconds = max(1, int(window_seconds))
        self._events: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str, now_ts: float) -> bool:
        events = self._events[key]
        window_start = now_ts - self.window_seconds
        while events and events[0] < window_start:
            events.popleft()
        if len(events) >= self.max_requests:
            return False
        events.append(now_ts)
        return True


_public_rate_limiter = _PublicRouteRateLimiter(
    max_requests=settings.public_rate_limit_requests,
    window_seconds=settings.public_rate_limit_window_sec,
)

app = FastAPI(
    title="ELLAN Order Pickup Service",
    version=get_version(),
    description=AUTHORIZATION_POLICY_MD,
)


# Routers principais
app.include_router(orders.router)
app.include_router(kiosk.router)
app.include_router(pickup.router)
app.include_router(partners.router)
app.include_router(logistics.router)
app.include_router(products.router)
app.include_router(pricing_fiscal.router)
app.include_router(integration_ops.router)
app.include_router(inventory.router)
app.include_router(internal.router)
app.include_router(dev_admin.router)
app.include_router(dev_base_catalog.router)
app.include_router(public_auth_router)
app.include_router(public_catalog_router)
app.include_router(public_me_router)
app.include_router(public_orders_router)
app.include_router(public_pickup_router)
app.include_router(public_fiscal_router)
# incluir public_orders e public_me se você quiser subir Sprint 1 mais limpo. Pode deixar para Sprint 2.

# Routers de health
app.include_router(health_router, tags=["Health"])
app.include_router(internal_health_router, tags=["Internal"])

app.include_router(payment_capabilities_router)


@app.middleware("http")
async def tracing_and_rate_limit_middleware(request: Request, call_next):
    trace_id = request.headers.get("X-Trace-Id") or str(uuid.uuid4())
    request.state.trace_id = trace_id
    started = time.time()

    path = str(request.url.path or "")
    if path.startswith("/public/"):
        client_ip = request.client.host if request.client else "unknown"
        rate_key = f"{client_ip}:{path}"
        if not _public_rate_limiter.allow(rate_key, started):
            return JSONResponse(
                status_code=429,
                content={
                    "service": "order_pickup_service",
                    "result": "error",
                    "error": {"type": "RATE_LIMIT_EXCEEDED", "message": "Too many requests"},
                    "trace_id": trace_id,
                },
                headers={"X-Trace-Id": trace_id},
            )

    response = await call_next(request)
    elapsed_ms = int((time.time() - started) * 1000)
    response.headers["X-Trace-Id"] = trace_id
    logger.info(
        "request_completed method=%s path=%s status=%s elapsed_ms=%s trace_id=%s",
        request.method,
        path,
        response.status_code,
        elapsed_ms,
        trace_id,
    )
    if int(response.status_code) >= 400:
        _record_dev_error_event(
            level="HTTP_ERROR",
            status_code=int(response.status_code),
            path=path,
            method=request.method,
            trace_id=trace_id,
        )
    return response


@app.get("/internal/dev/errors")
async def internal_dev_errors(request: Request):
    if not _is_dev_env():
        return JSONResponse(status_code=404, content={"ok": False, "message": "dev errors endpoint disabled"})
    token = request.headers.get("X-Internal-Token")
    if token != settings.internal_token:
        return JSONResponse(status_code=403, content={"ok": False, "message": "forbidden"})
    return {"ok": True, "count": len(_dev_error_events), "items": list(_dev_error_events)}


@app.post("/internal/mock/webhook-ok")
async def internal_mock_webhook_ok(request: Request):
    # Endpoint de apoio para validação E2E local dos workers de webhook.
    if str(settings.node_env).lower() not in {"dev", "development", "local", "test"}:
        return JSONResponse(status_code=404, content={"ok": False, "message": "mock endpoint disabled"})
    payload = await request.body()
    return {
        "ok": True,
        "message": "mock webhook accepted",
        "received_bytes": len(payload or b""),
    }


@app.post("/internal/mock/webhook-fail")
async def internal_mock_webhook_fail():
    # Endpoint de apoio para falha controlada (5xx) em E2E local.
    if str(settings.node_env).lower() not in {"dev", "development", "local", "test"}:
        return JSONResponse(status_code=404, content={"ok": False, "message": "mock endpoint disabled"})
    return JSONResponse(
        status_code=500,
        content={"ok": False, "message": "mock webhook forced failure"},
    )




# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=_resolve_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

expiry_task: asyncio.Task | None = None
lifecycle_events_task: asyncio.Task | None = None
reconciliation_retry_task: asyncio.Task | None = None
inventory_reservation_expiry_task: asyncio.Task | None = None
inventory_reserved_reconciliation_task: asyncio.Task | None = None
integration_order_events_outbox_task: asyncio.Task | None = None


@app.on_event("startup")
async def startup():
    if not _is_dev_env():
        if str(settings.internal_token or "").strip() == "dev-internal-token":
            raise RuntimeError("INTERNAL_TOKEN default não permitido fora de dev/local.")
        if str(settings.jwt_secret or "").strip() == "CHANGE_ME_IN_PROD":
            raise RuntimeError("JWT_SECRET default não permitido fora de dev/local.")
    init_db()

    required_modules = [
        "app.schemas.kiosk",
        "app.jobs.lifecycle_events_consumer",
        "app.schemas.dev_admin",
        "app.routers.dev_admin",
    ]
    for module in required_modules:
        try:
            __import__(module)
            logger.info("✅ Módulo %s carregado com sucesso", module)
        except ImportError as e:
            logger.exception("❌ Erro ao carregar %s: %s", module, e)
            raise

    global expiry_task
    if expiry_task is None:
        expiry_task = asyncio.create_task(expiry_loop(), name="expiry_loop")

    global lifecycle_events_task
    if lifecycle_events_task is None:
        lifecycle_events_task = asyncio.create_task(
            lifecycle_events_loop(),
            name="lifecycle_events_loop",
        )

    global reconciliation_retry_task
    if reconciliation_retry_task is None:
        reconciliation_retry_task = asyncio.create_task(
            reconciliation_retry_loop(),
            name="reconciliation_retry_loop",
        )

    global inventory_reservation_expiry_task
    if inventory_reservation_expiry_task is None:
        inventory_reservation_expiry_task = asyncio.create_task(
            inventory_reservations_expiry_loop(),
            name="inventory_reservations_expiry_loop",
        )

    global inventory_reserved_reconciliation_task
    if inventory_reserved_reconciliation_task is None:
        inventory_reserved_reconciliation_task = asyncio.create_task(
            inventory_reserved_reconciliation_loop(),
            name="inventory_reserved_reconciliation_loop",
        )

    global integration_order_events_outbox_task
    if integration_order_events_outbox_task is None:
        integration_order_events_outbox_task = asyncio.create_task(
            integration_order_events_outbox_loop(),
            name="integration_order_events_outbox_loop",
        )


@app.on_event("shutdown")
async def shutdown():
    global expiry_task
    if expiry_task:
        expiry_task.cancel()
        try:
            await expiry_task
        except asyncio.CancelledError:
            pass
        expiry_task = None

    global lifecycle_events_task
    if lifecycle_events_task:
        lifecycle_events_task.cancel()
        try:
            await lifecycle_events_task
        except asyncio.CancelledError:
            pass
        lifecycle_events_task = None

    global reconciliation_retry_task
    if reconciliation_retry_task:
        reconciliation_retry_task.cancel()
        try:
            await reconciliation_retry_task
        except asyncio.CancelledError:
            pass
        reconciliation_retry_task = None

    global inventory_reservation_expiry_task
    if inventory_reservation_expiry_task:
        inventory_reservation_expiry_task.cancel()
        try:
            await inventory_reservation_expiry_task
        except asyncio.CancelledError:
            pass
        inventory_reservation_expiry_task = None

    global inventory_reserved_reconciliation_task
    if inventory_reserved_reconciliation_task:
        inventory_reserved_reconciliation_task.cancel()
        try:
            await inventory_reserved_reconciliation_task
        except asyncio.CancelledError:
            pass
        inventory_reserved_reconciliation_task = None

    global integration_order_events_outbox_task
    if integration_order_events_outbox_task:
        integration_order_events_outbox_task.cancel()
        try:
            await integration_order_events_outbox_task
        except asyncio.CancelledError:
            pass
        integration_order_events_outbox_task = None


async def expiry_loop():
    while True:
        db = SessionLocal()
        try:
            await asyncio.to_thread(run_expiry_once, db)
        except Exception:
            logger.exception("expiry job failed")
        finally:
            db.close()

        await asyncio.sleep(settings.expiry_poll_sec)


async def lifecycle_events_loop():
    while True:
        db = SessionLocal()
        try:
            await asyncio.to_thread(run_lifecycle_events_consumer_once, db)
        except Exception:
            logger.exception("lifecycle events consumer failed")
        finally:
            db.close()

        await asyncio.sleep(settings.lifecycle_events_poll_sec)


async def reconciliation_retry_loop():
    while True:
        db = SessionLocal()
        try:
            await asyncio.to_thread(
                run_reconciliation_retry_once,
                db,
                batch_size=settings.reconciliation_retry_batch_size,
            )
        except Exception:
            logger.exception("reconciliation retry loop failed")
        finally:
            db.close()

        await asyncio.sleep(settings.reconciliation_retry_poll_sec)


async def inventory_reservations_expiry_loop():
    while True:
        db = SessionLocal()
        try:
            await asyncio.to_thread(run_inventory_reservations_expiry_once, db)
        except Exception:
            logger.exception("inventory reservations expiry loop failed")
        finally:
            db.close()

        await asyncio.sleep(settings.inventory_reservation_expiry_poll_sec)


async def inventory_reserved_reconciliation_loop():
    while True:
        db = SessionLocal()
        try:
            await asyncio.to_thread(run_inventory_reserved_reconciliation_once, db)
        except Exception:
            logger.exception("inventory reserved reconciliation loop failed")
        finally:
            db.close()

        await asyncio.sleep(settings.inventory_reserved_reconciliation_poll_sec)


async def integration_order_events_outbox_loop():
    while True:
        db = SessionLocal()
        try:
            await asyncio.to_thread(
                run_integration_order_events_outbox_once,
                db,
                batch_size=settings.integration_order_events_outbox_batch_size,
                max_attempts=settings.integration_order_events_outbox_max_attempts,
                base_backoff_sec=settings.integration_order_events_outbox_base_backoff_sec,
            )
        except Exception:
            logger.exception("integration order events outbox loop failed")
        finally:
            db.close()

        await asyncio.sleep(settings.integration_order_events_outbox_poll_sec)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    trace_id = getattr(request.state, "trace_id", None) or str(uuid.uuid4())
    logger.exception(
        "unhandled_exception path=%s trace_id=%s error_type=%s",
        str(request.url.path),
        trace_id,
        exc.__class__.__name__,
    )
    _record_dev_error_event(
        level="UNHANDLED_EXCEPTION",
        status_code=500,
        path=str(request.url.path),
        method=request.method,
        trace_id=trace_id,
        error_type=exc.__class__.__name__,
        message=str(exc)[:300],
    )
    return JSONResponse(
        status_code=500,
        content={
            "service": "order_pickup_service",
            "result": "error",
            "error": {"type": exc.__class__.__name__, "message": "Internal server error"},
            "severity": "HIGH",
            "severity_code": "GATEWAY_UNHANDLED_EXCEPTION",
            "timestamp": time.time(),
            "trace_id": trace_id,
        },
        headers={"X-Trace-Id": trace_id},
    )