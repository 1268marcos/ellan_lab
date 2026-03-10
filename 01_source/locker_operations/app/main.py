from fastapi import FastAPI

from app.api.routers.health import router as health_router
from app.api.routers.lockers import router as lockers_router
from app.core.logging import configure_logging
from app.core.middleware import RequestContextMiddleware

configure_logging()

app = FastAPI(title="locker_operations")
app.add_middleware(RequestContextMiddleware)
app.include_router(health_router)
app.include_router(lockers_router)
