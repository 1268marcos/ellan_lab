# 01_source/order_pickup_service/app/main.py
import asyncio
import logging
import time
import traceback

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.db import SessionLocal, init_db
from app.core.version import get_version
from app.health.health import router as health_router
from app.health.internal import router as internal_health_router
from app.jobs.expiry import run_expiry_once
from app.jobs.lifecycle_events_consumer import run_lifecycle_events_consumer_once
from app.routers import dev_admin, internal, kiosk, orders, pickup

from app.routers.public_auth import router as public_auth_router
from app.routers.public_catalog import router as public_catalog_router
from app.routers.public_orders import router as public_orders_router
from app.routers.public_pickup import router as public_pickup_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("order_pickup_service")

app = FastAPI(
    title="ELLAN Order Pickup Service",
    version=get_version(),
)

# Routers principais
app.include_router(orders.router)
app.include_router(kiosk.router)
app.include_router(pickup.router)
app.include_router(internal.router)
app.include_router(dev_admin.router)
app.include_router(public_auth_router)
app.include_router(public_catalog_router)
app.include_router(public_orders_router)
app.include_router(public_pickup_router)
# incluir public_orders e public_me se você quiser subir Sprint 1 mais limpo. Pode deixar para Sprint 2.

# Routers de health
app.include_router(health_router, tags=["Health"])
app.include_router(internal_health_router, tags=["Internal"])

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://taki.pt",
        "https://molrealestate.pt",
        "https://queroterreno.pt",
        "https://propertypartners.pt",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

expiry_task: asyncio.Task | None = None
lifecycle_events_task: asyncio.Task | None = None


@app.on_event("startup")
async def startup():
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


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "service": "order_pickup_service",
            "result": "error",
            "error": {"type": exc.__class__.__name__, "message": str(exc)},
            "severity": "HIGH",
            "severity_code": "GATEWAY_UNHANDLED_EXCEPTION",
            "timestamp": time.time(),
            "debug": {
                "path": str(request.url.path),
                "traceback": traceback.format_exc().splitlines()[-40:],
            },
        },
    )