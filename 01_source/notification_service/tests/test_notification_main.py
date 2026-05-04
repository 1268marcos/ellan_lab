from unittest.mock import MagicMock

from fastapi.testclient import TestClient


def test_lifespan_redis_down(monkeypatch):
    import redis as redis_mod

    monkeypatch.setattr(redis_mod.Redis, "from_url", staticmethod(lambda *a, **k: (_ for _ in ()).throw(RuntimeError("down"))))
    from app.main import app

    with TestClient(app) as c:
        assert c.app.state.redis is None


def test_lifespan_close_raises(monkeypatch):
    import redis as redis_mod

    m = MagicMock()
    m.ping.return_value = True
    m.close.side_effect = RuntimeError("x")
    monkeypatch.setattr(redis_mod.Redis, "from_url", staticmethod(lambda *a, **k: m))
    from app.main import app

    with TestClient(app):
        pass
