# 01_source/backend/order_lifecycle_service/app/main.py
from fastapi import FastAPI

from app.core.config import settings
from app.core.db import init_db
from app.core.logging import configure_logging
from app.routers.health import router as health_router
from app.routers.internal import router as internal_router

configure_logging()

app = FastAPI(
    title="order_lifecycle_service",
    version="0.1.0",
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


app.include_router(health_router)
app.include_router(internal_router)


@app.get("/")
def root():
    return {
        "service": settings.service_name,
        "status": "ok",
        "environment": settings.app_env,
    }