"""Testes unitários de AntifraudCache (Redis + fallback em memória)."""
import json
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from app.services.antifraud_service import AntifraudCache


def _cache_with_mock_redis(mock_redis: MagicMock) -> AntifraudCache:
    mock_redis.ping.return_value = True
    with patch("app.services.antifraud_service.redis.Redis", return_value=mock_redis):
        return AntifraudCache()


def test_set_get_redis_with_ttl():
    mock_redis = MagicMock()
    cache = _cache_with_mock_redis(mock_redis)
    assert cache._ok is True

    payload = {"count": 3, "region": "SP"}
    cache.set("af:velocity:user-1", payload, ttl_seconds=120)

    mock_redis.setex.assert_called_once_with(
        "af:velocity:user-1",
        120,
        json.dumps(payload),
    )

    mock_redis.get.return_value = json.dumps(payload)
    assert cache.get("af:velocity:user-1") == payload
    mock_redis.get.assert_called_once_with("af:velocity:user-1")


def test_memory_fallback_expires_after_ttl():
    with patch(
        "app.services.antifraud_service.redis.Redis",
        side_effect=ConnectionError("redis down"),
    ):
        cache = AntifraudCache()

    assert cache._ok is False
    cache.set("af:expiring", "value", ttl_seconds=3600)
    cache._memory_expiry["af:expiring"] = datetime.now(timezone.utc) - timedelta(seconds=1)

    assert cache.get("af:expiring") is None
    assert "af:expiring" not in cache._memory_cache


def test_increment_redis_pipeline():
    mock_redis = MagicMock()
    mock_pipe = MagicMock()
    mock_redis.pipeline.return_value = mock_pipe
    mock_pipe.execute.return_value = [7, True]

    cache = _cache_with_mock_redis(mock_redis)
    result = cache.increment("af:cnt:device-x", delta=2, ttl_seconds=90)

    assert result == 7
    mock_pipe.incrby.assert_called_once_with("af:cnt:device-x", 2)
    mock_pipe.expire.assert_called_once_with("af:cnt:device-x", 90)
    mock_pipe.execute.assert_called_once()


def test_increment_memory_fallback():
    with patch(
        "app.services.antifraud_service.redis.Redis",
        side_effect=OSError("unavailable"),
    ):
        cache = AntifraudCache()

    assert cache.increment("af:mem:cnt", delta=1, ttl_seconds=60) == 1
    assert cache.increment("af:mem:cnt", delta=4, ttl_seconds=60) == 5
    assert cache.get("af:mem:cnt") == 5


def test_fallback_when_redis_unavailable_on_init():
    with patch(
        "app.services.antifraud_service.redis.Redis",
        side_effect=ConnectionError("cannot connect"),
    ):
        cache = AntifraudCache()

    assert cache._ok is False
    cache.set("af:fallback", {"ok": True}, ttl_seconds=30)
    assert cache.get("af:fallback") == {"ok": True}


def test_degrades_to_memory_when_redis_fails_at_runtime():
    mock_redis = MagicMock()
    cache = _cache_with_mock_redis(mock_redis)

    mock_redis.setex.side_effect = RuntimeError("connection reset")
    cache.set("af:degraded", [1, 2, 3], ttl_seconds=45)

    assert cache._ok is False
    assert cache.get("af:degraded") == [1, 2, 3]
    mock_redis.setex.assert_called_once()


def test_delete_clears_memory_even_when_redis_fails():
    mock_redis = MagicMock()
    cache = _cache_with_mock_redis(mock_redis)

    cache._memory_cache["af:del"] = "x"
    cache._memory_expiry["af:del"] = datetime.now(timezone.utc) + timedelta(hours=1)
    mock_redis.delete.side_effect = RuntimeError("redis gone")

    cache.delete("af:del")

    assert cache._ok is False
    assert "af:del" not in cache._memory_cache
    assert "af:del" not in cache._memory_expiry
