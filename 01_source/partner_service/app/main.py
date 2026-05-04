from __future__ import annotations

import logging
from contextlib import asynccontextmanager

import redis
from fastapi import FastAPI, Request
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from app.core.config import get_settings
from app.core.database import init_db
from app.core.health import health_payload
from app.routers import compatibility, lockers, partners, webhooks
from app.services.rate_limiter import sync_check_and_increment

logger = logging.getLogger(__name__)


def _should_skip_rate_limit(path: str) -> bool:
    skip = ("/api/v1/health", "/metrics", "/docs", "/openapi.json", "/redoc")
    return any(path.startswith(p) for p in skip)


def _partner_id_for_rate_limit(path: str, _request: Request) -> str | None:
    parts = path.strip("/").split("/")
    try:
        idx = parts.index("partners")
    except ValueError:
        return None
    if idx + 1 < len(parts):
        candidate = parts[idx + 1]
        if candidate and candidate not in ("openapi.json",):
            return candidate
    return None


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if _should_skip_rate_limit(path):
            return await call_next(request)
        settings = get_settings()
        redis_client = request.app.state.redis_sync
        partner_id = _partner_id_for_rate_limit(path, request)
        if partner_id is None:
            partner_id = f"ip:{request.client.host}" if request.client else "ip:unknown"
        allowed, _ = sync_check_and_increment(
            redis_client,
            partner_id=partner_id,
            limit_per_minute=settings.rate_limit_per_minute,
        )
        if not allowed:
            return JSONResponse(status_code=429, content={"detail": "rate limit exceeded"})
        return await call_next(request)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    settings = get_settings()
    app.state.redis_sync = redis.Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        yield
    finally:
        app.state.redis_sync.close()


app = FastAPI(title="partner-service", lifespan=lifespan)
app.add_middleware(RateLimitMiddleware)
app.include_router(partners.router, prefix="/api/v1")
app.include_router(webhooks.router, prefix="/api/v1")
app.include_router(lockers.router, prefix="/api/v1")
app.include_router(compatibility.router, prefix="/api/v1")


@app.get("/api/v1/health")
def health_check():
    return health_payload()


@app.get("/metrics")
def prometheus_metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
