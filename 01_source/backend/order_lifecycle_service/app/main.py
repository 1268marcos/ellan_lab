from fastapi import FastAPI

from app.core.logging import configure_logging
from app.routers.health import router as health_router
from app.routers.internal import router as internal_router
from app.core.config import settings

configure_logging()

app = FastAPI(
    title="order_lifecycle_service",
    version="0.1.0",
)

app.include_router(health_router)
app.include_router(internal_router)


@app.get("/")
def root():
    return {
        "service": settings.service_name,
        "status": "ok",
        "environment": settings.app_env,
    }