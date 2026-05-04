from fastapi.testclient import TestClient


def test_lifespan_redis_connection_failure(monkeypatch):
    import app.main as main_mod

    class BoomRedis:
        @staticmethod
        def from_url(*_a, **_k):
            raise RuntimeError("redis down")

        def ping(self):
            return True

        def close(self):
            return None

    monkeypatch.setattr(main_mod, "Redis", BoomRedis)
    with TestClient(main_mod.app) as c:
        assert c.app.state.redis is None
