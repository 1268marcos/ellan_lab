import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import fakeredis  # noqa: E402
import redis  # noqa: E402


def _fake_from_url(url: str, **kwargs):  # noqa: ARG001
    return fakeredis.FakeRedis(decode_responses=kwargs.get("decode_responses", False))


redis.Redis.from_url = _fake_from_url  # type: ignore[method-assign]

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture()
def client() -> TestClient:
    with TestClient(app) as c:
        yield c
