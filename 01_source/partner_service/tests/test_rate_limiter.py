from __future__ import annotations

import fakeredis

from app.services.rate_limiter import sync_check_and_increment


def test_sync_check_and_increment_under_limit():
    r = fakeredis.FakeRedis(decode_responses=True)
    allowed, count = sync_check_and_increment(r, partner_id="p1", limit_per_minute=100)
    assert allowed is True
    assert count == 1


def test_sync_check_exceeds():
    r = fakeredis.FakeRedis(decode_responses=True)
    for _ in range(3):
        allowed, count = sync_check_and_increment(r, partner_id="p2", limit_per_minute=2)
    assert allowed is False
    assert count == 3
