from __future__ import annotations

import importlib.util
import os
from contextlib import asynccontextmanager
from pathlib import Path

import redis
from fastapi import FastAPI

from app.core.config import get_settings
from app.core.database import init_db
from app.routers import health, notifications, templates


def _maybe_mtls(app_: FastAPI) -> None:
    if os.getenv("MTLS_ENFORCE", "0") != "1":
        return
    path = Path(__file__).resolve().parents[2] / "inventory_service" / "infra" / "mtls" / "middleware.py"
    if not path.is_file():
        return
    spec = importlib.util.spec_from_file_location("inv_mtls_middleware", path)
    if spec is None or spec.loader is None:
        return
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.maybe_add_mtls(app_, ca_file=os.getenv("MTLS_CA_FILE"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    settings = get_settings()
    try:
        app.state.redis = redis.Redis.from_url(settings.redis_url, decode_responses=False)
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


app = FastAPI(title="notification-service", lifespan=lifespan)
_maybe_mtls(app)
app.include_router(health.router)
app.include_router(notifications.router)
app.include_router(templates.router)
