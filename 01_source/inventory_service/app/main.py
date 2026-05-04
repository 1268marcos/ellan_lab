from contextlib import asynccontextmanager

from fastapi import FastAPI
from redis import Redis

from app.core.config import get_settings
from app.core.database import init_db
from app.routers import dlq, health, inventory, reconciliation, reservations


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    settings = get_settings()
    try:
        app.state.redis = Redis.from_url(settings.redis_url, decode_responses=False)
        app.state.redis.ping()
    except Exception:
        app.state.redis = None
    yield
    r = getattr(app.state, "redis", None)
    if r is not None:
        try:
            r.close()
        except Exception:
            pass


app = FastAPI(title="inventory-service", lifespan=lifespan)
app.include_router(health.router)
app.include_router(inventory.router)
app.include_router(reservations.router)
app.include_router(reconciliation.router)
app.include_router(dlq.router)
