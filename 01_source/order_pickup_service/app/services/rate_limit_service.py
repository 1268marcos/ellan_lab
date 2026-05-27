from __future__ import annotations

import logging
import os
import time
from typing import Any, Protocol

from app.core.config import settings

logger = logging.getLogger(__name__)

_KEY_PREFIX = "rl"


class RateLimiter(Protocol):
    def is_allowed(self, key: str) -> tuple[bool, int]: ...

    def record_failure(self, key: str) -> None: ...

    def clear(self, key: str) -> None: ...


class RedisRateLimiter:
    """
    Rate limiter distribuído com Redis.

    Estratégia:
    - Contador de falhas: ``INCR`` + ``EXPIRE`` (janela deslizante por TTL).
    - Bloqueio após ``max_attempts``: ``SET key NX EX block_seconds``.
    - ``is_allowed``: ``TTL`` na chave de bloqueio para ``retry_after_sec``.
    """

    def __init__(
        self,
        redis_client: Any,
        window_seconds: int,
        max_attempts: int,
        *,
        block_seconds: int | None = None,
    ) -> None:
        self._redis = redis_client
        self._window_seconds = max(int(window_seconds), 1)
        self._max_attempts = max(int(max_attempts), 1)
        self._block_seconds = max(
            int(block_seconds if block_seconds is not None else window_seconds),
            1,
        )

    def _count_key(self, key: str) -> str:
        return f"{_KEY_PREFIX}:cnt:{key}"

    def _block_key(self, key: str) -> str:
        return f"{_KEY_PREFIX}:block:{key}"

    def is_allowed(self, key: str) -> tuple[bool, int]:
        block_key = self._block_key(key)
        try:
            ttl = int(self._redis.ttl(block_key))
        except Exception as exc:
            logger.warning(
                "rate_limiter_ttl_failed key=%s error=%s",
                key,
                exc.__class__.__name__,
            )
            return True, 0

        if ttl > 0:
            return False, ttl
        if ttl == -1:
            return False, self._block_seconds
        return True, 0

    def record_failure(self, key: str) -> None:
        cnt_key = self._count_key(key)
        block_key = self._block_key(key)
        try:
            count = int(self._redis.incr(cnt_key))
            if count == 1:
                self._redis.expire(cnt_key, self._window_seconds)
            if count >= self._max_attempts:
                self._redis.set(block_key, "1", nx=True, ex=self._block_seconds)
        except Exception as exc:
            logger.warning(
                "rate_limiter_record_failure_failed key=%s error=%s",
                key,
                exc.__class__.__name__,
            )

    def clear(self, key: str) -> None:
        try:
            self._redis.delete(self._count_key(key), self._block_key(key))
        except Exception as exc:
            logger.warning(
                "rate_limiter_clear_failed key=%s error=%s",
                key,
                exc.__class__.__name__,
            )


class MemoryRateLimiter:
    """Fallback em processo quando Redis não está configurado (dev / teste)."""

    def __init__(
        self,
        window_seconds: int,
        max_attempts: int,
        *,
        block_seconds: int | None = None,
    ) -> None:
        self._window_seconds = max(int(window_seconds), 1)
        self._max_attempts = max(int(max_attempts), 1)
        self._block_seconds = max(
            int(block_seconds if block_seconds is not None else window_seconds),
            1,
        )
        self._entries: dict[str, dict[str, Any]] = {}

    def is_allowed(self, key: str) -> tuple[bool, int]:
        now = int(time.time())
        entry = self._entries.get(key)
        if not entry:
            return True, 0

        blocked_until = entry.get("blocked_until")
        if blocked_until and now < int(blocked_until):
            return False, int(blocked_until) - now
        return True, 0

    def record_failure(self, key: str) -> None:
        now = int(time.time())
        entry = self._entries.get(key, {"fails": [], "blocked_until": None})
        fails = [ts for ts in entry.get("fails", []) if now - int(ts) <= self._window_seconds]
        fails.append(now)

        blocked_until = None
        if len(fails) >= self._max_attempts:
            blocked_until = now + self._block_seconds

        self._entries[key] = {
            "fails": fails,
            "blocked_until": blocked_until,
        }

    def clear(self, key: str) -> None:
        self._entries.pop(key, None)


_REDIS_CLIENT: Any | None = None
_REDIS_ATTEMPTED = False
_MANUAL_REDEEM_LIMITER: RateLimiter | None = None


def _resolve_redis_client() -> Any | None:
    global _REDIS_CLIENT, _REDIS_ATTEMPTED
    if _REDIS_ATTEMPTED:
        return _REDIS_CLIENT
    _REDIS_ATTEMPTED = True

    try:
        import redis  # type: ignore[import-untyped]
    except ImportError:
        logger.info("rate_limiter_redis_package_missing_using_memory_fallback")
        return None

    redis_url = str(getattr(settings, "catalog_redis_url", "") or "").strip()
    redis_host = str(os.getenv("REDIS_INTERNAL", "")).strip()

    try:
        if redis_url:
            _REDIS_CLIENT = redis.from_url(
                redis_url,
                decode_responses=False,
                socket_timeout=0.5,
                socket_connect_timeout=0.5,
            )
            _REDIS_CLIENT.ping()
            logger.info("rate_limiter_redis_connected_via_url")
            return _REDIS_CLIENT
        if redis_host:
            _REDIS_CLIENT = redis.Redis(
                host=redis_host,
                port=6379,
                db=0,
                socket_timeout=0.5,
                socket_connect_timeout=0.5,
            )
            _REDIS_CLIENT.ping()
            logger.info("rate_limiter_redis_connected_via_host")
            return _REDIS_CLIENT
    except Exception as exc:
        logger.warning(
            "rate_limiter_redis_unavailable_using_memory_fallback error=%s",
            exc.__class__.__name__,
        )
        _REDIS_CLIENT = None

    return None


def build_manual_redeem_rate_limiter() -> RateLimiter:
    redis_client = _resolve_redis_client()
    window_seconds = int(settings.manual_redeem_window_sec)
    max_attempts = int(settings.manual_redeem_max_attempts)
    block_seconds = int(settings.manual_redeem_block_sec)

    if redis_client is not None:
        return RedisRateLimiter(
            redis_client,
            window_seconds,
            max_attempts,
            block_seconds=block_seconds,
        )
    return MemoryRateLimiter(
        window_seconds,
        max_attempts,
        block_seconds=block_seconds,
    )


def get_manual_redeem_rate_limiter() -> RateLimiter:
    global _MANUAL_REDEEM_LIMITER
    if _MANUAL_REDEEM_LIMITER is None:
        _MANUAL_REDEEM_LIMITER = build_manual_redeem_rate_limiter()
    return _MANUAL_REDEEM_LIMITER
