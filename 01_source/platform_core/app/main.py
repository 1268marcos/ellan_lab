from fastapi import FastAPI

from app.api.routers.health import router as health_router
from app.api.routers.tenants import router as tenants_router
from app.core.logging import configure_logging
from app.core.middleware import RequestContextMiddleware

configure_logging()

app = FastAPI(title="platform_core")
app.add_middleware(RequestContextMiddleware)
app.include_router(health_router)
app.include_router(tenants_router)
