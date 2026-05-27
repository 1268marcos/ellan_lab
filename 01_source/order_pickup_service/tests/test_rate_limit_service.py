from __future__ import annotations

import pytest

from app.services.rate_limit_service import MemoryRateLimiter, RedisRateLimiter

try:
    import fakeredis
except ImportError:
    fakeredis = None  # type: ignore[assignment]


@pytest.fixture()
def memory_limiter():
    return MemoryRateLimiter(window_seconds=120, max_attempts=3, block_seconds=300)


def test_memory_limiter_blocks_after_max_failures(memory_limiter):
    key = "PT:123456:1.2.3.4"
    assert memory_limiter.is_allowed(key) == (True, 0)

    memory_limiter.record_failure(key)
    memory_limiter.record_failure(key)
    assert memory_limiter.is_allowed(key) == (True, 0)

    memory_limiter.record_failure(key)
    allowed, retry_after = memory_limiter.is_allowed(key)
    assert allowed is False
    assert retry_after > 0


def test_memory_limiter_clear_resets(memory_limiter):
    key = "PT:123456:1.2.3.4"
    for _ in range(3):
        memory_limiter.record_failure(key)
    assert memory_limiter.is_allowed(key)[0] is False

    memory_limiter.clear(key)
    assert memory_limiter.is_allowed(key) == (True, 0)


@pytest.mark.skipif(fakeredis is None, reason="fakeredis não instalado")
def test_redis_limiter_uses_incr_expire_and_block_nx():
    redis_client = fakeredis.FakeRedis(decode_responses=False)
    limiter = RedisRateLimiter(
        redis_client,
        window_seconds=60,
        max_attempts=2,
        block_seconds=90,
    )
    key = "region:code:ip"

    assert limiter.is_allowed(key) == (True, 0)
    limiter.record_failure(key)
    assert limiter.is_allowed(key) == (True, 0)
    limiter.record_failure(key)

    allowed, retry_after = limiter.is_allowed(key)
    assert allowed is False
    assert 0 < retry_after <= 90

    limiter.clear(key)
    assert limiter.is_allowed(key) == (True, 0)
