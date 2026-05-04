from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("RATE_LIMIT_PER_MINUTE", "5000")

import fakeredis  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture(autouse=True)
def clear_settings_cache():
    from app.core.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def fake_redis():
    return fakeredis.FakeRedis(decode_responses=True)


@pytest.fixture
def client(monkeypatch, fake_redis):
    import redis

    monkeypatch.setattr(redis.Redis, "from_url", lambda *a, **k: fake_redis)
    from app.core.config import get_settings
    from app.main import app

    get_settings.cache_clear()
    with TestClient(app) as c:
        yield c
    fake_redis.flushall()
