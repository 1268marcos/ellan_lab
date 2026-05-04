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


@pytest.fixture(autouse=True)
def _default_sla_and_locker(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.integrations import backend_runtime, order_lifecycle

    if "test_integrations.py" not in str(request.fspath):
        monkeypatch.setattr(order_lifecycle, "fetch_sla_deadlines", lambda c=None: {"ok": True, "deadlines": []})
        monkeypatch.setattr(backend_runtime, "get_locker_status", lambda lid, c=None: {"ok": True, "data": {}})


@pytest.fixture()
def client() -> TestClient:
    with TestClient(app) as c:
        yield c
