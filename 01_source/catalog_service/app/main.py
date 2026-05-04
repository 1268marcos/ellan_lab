from __future__ import annotations

import importlib.util
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import redis
from fastapi import Depends, FastAPI, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import SessionLocal, get_db, init_db
from app.core.health import health_payload
from app.events import replay
from app.middleware.cache import CacheStatusMiddleware
from app.routers import categories, compatibility, lockers, products, webhooks
from app.schemas.webhook import ReplayIn
from app.services import catalog_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        catalog_service.seed_defaults(db)
    finally:
        db.close()
    settings = get_settings()
    app.state.redis_sync = redis.Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        yield
    finally:
        app.state.redis_sync.close()


app = FastAPI(title="catalog-service", lifespan=lifespan)


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


_maybe_mtls(app)
app.add_middleware(CacheStatusMiddleware)
app.include_router(products.router, prefix="/api/v1")
app.include_router(categories.router, prefix="/api/v1")
app.include_router(lockers.router, prefix="/api/v1")
app.include_router(compatibility.router, prefix="/api/v1")
app.include_router(webhooks.router, prefix="/api/v1")


@app.get("/api/v1/health")
def health():
    return health_payload()


@app.get("/health/ready")
def health_ready(request: Request):
    try:
        request.app.state.redis_sync.ping()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="redis_unavailable") from exc
    return {"status": "ready"}


@app.get("/health/live")
def health_live():
    return {"status": "alive"}


def get_redis(request: Request) -> Any:
    return request.app.state.redis_sync


@app.post("/api/v1/events/replay")
def events_replay(
    body: ReplayIn,
    db: Session = Depends(get_db),
    redis: Any = Depends(get_redis),
) -> dict[str, int]:
    def handler(session: Session, et: str, pl: dict) -> None:
        catalog_service.apply_stream_event(session, et, pl)

    n = replay.replay_range(redis, db, handler=handler, start_id=body.start_id, count=body.count)
    return {"replayed": n}
