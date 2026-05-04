import importlib

import pytest
from fastapi.testclient import TestClient


def test_mtls_enforced_reload(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MTLS_ENFORCE", "1")
    import app.main as mm

    importlib.reload(mm)
    c = TestClient(mm.app)
    assert c.get("/health").status_code == 403
    assert c.get("/health", headers={"X-mTLS-Subject": "CN=t"}).status_code == 200
    monkeypatch.setenv("MTLS_ENFORCE", "0")
    importlib.reload(mm)
