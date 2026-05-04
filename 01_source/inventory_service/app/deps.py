from fastapi import Depends, Header, Request
from redis import Redis

from app.services.idempotency import IdempotencyStore


def get_redis(request: Request) -> Redis | None:
    return getattr(request.app.state, "redis", None)


def get_idempotency_store(request: Request) -> IdempotencyStore:
    r = get_redis(request)
    return IdempotencyStore(r)


def idempotency_key_header(x_idempotency_key: str | None = Header(default=None, alias="X-Idempotency-Key")) -> str | None:
    return x_idempotency_key
