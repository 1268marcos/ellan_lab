from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

import fakeredis  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture(autouse=True)
def clear_settings():
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
    from app.core.database import Base, SessionLocal, engine
    from app.main import app
    from app.models.compatibility import Locker
    from app.services import catalog_service

    get_settings.cache_clear()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        catalog_service.seed_defaults(db)
        db.add(
            Locker(
                id="locker-m-001",
                partner_id="11111111-1111-1111-1111-111111111111",
                site_id="s1",
                slot_size="M",
                max_weight_g=5000,
            )
        )
        db.commit()
    finally:
        db.close()
    with TestClient(app) as c:
        yield c
    fake_redis.flushall()
