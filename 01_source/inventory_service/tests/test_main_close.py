from unittest.mock import MagicMock

from fastapi.testclient import TestClient


def test_lifespan_close_failure_is_swallowed(monkeypatch):
    import app.main as main_mod

    m = MagicMock()
    m.ping.return_value = True
    m.close.side_effect = RuntimeError("close boom")
    monkeypatch.setattr(main_mod.Redis, "from_url", staticmethod(lambda *a, **k: m))
    with TestClient(main_mod.app):
        pass
