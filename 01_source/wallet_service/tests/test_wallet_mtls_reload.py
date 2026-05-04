import importlib

from fastapi.testclient import TestClient


def test_mtls_enforced_reload(monkeypatch):
    monkeypatch.setenv("MTLS_ENFORCE", "1")
    import app.main as mm

    importlib.reload(mm)
    c = TestClient(mm.app)
    assert c.get("/api/v1/health").status_code == 403
    assert c.get("/api/v1/health", headers={"X-mTLS-Subject": "CN=t"}).status_code == 200
    monkeypatch.setenv("MTLS_ENFORCE", "0")
    importlib.reload(mm)

