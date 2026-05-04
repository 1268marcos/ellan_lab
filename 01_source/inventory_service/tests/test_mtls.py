import os

from fastapi import FastAPI
from fastapi.testclient import TestClient

from infra.mtls.client import build_ssl_context, mtls_client
from infra.mtls.middleware import MTLSMiddleware, maybe_add_mtls


def test_mtls_middleware_allows_without_enforce():
    app = FastAPI()

    @app.get("/x")
    def x():
        return {"ok": True}

    app.add_middleware(MTLSMiddleware, ca_file="")
    c = TestClient(app)
    assert c.get("/x").status_code == 200


def test_mtls_middleware_blocks_without_header(monkeypatch):
    monkeypatch.setenv("MTLS_ENFORCE", "1")
    app = FastAPI()

    @app.get("/api/v1/x")
    def x():
        return {"ok": True}

    app.add_middleware(MTLSMiddleware, ca_file="")
    c = TestClient(app)
    r = c.get("/api/v1/x")
    assert r.status_code == 403


def test_mtls_middleware_ok_with_subject(monkeypatch):
    monkeypatch.setenv("MTLS_ENFORCE", "1")
    app = FastAPI()

    @app.get("/api/v1/x")
    def x():
        return {"ok": True}

    app.add_middleware(MTLSMiddleware, ca_file="")
    c = TestClient(app)
    r = c.get("/api/v1/x", headers={"X-mTLS-Subject": "CN=test"})
    assert r.status_code == 200


def test_maybe_add_mtls(monkeypatch):
    monkeypatch.setenv("MTLS_ENFORCE", "0")
    app = FastAPI()

    @app.get("/z")
    def z():
        return {"z": 1}

    maybe_add_mtls(app)
    assert TestClient(app).get("/z").status_code == 200


def test_maybe_add_mtls_enforces(monkeypatch):
    monkeypatch.setenv("MTLS_ENFORCE", "1")
    app = FastAPI()

    @app.get("/api/v1/h")
    def h():
        return {"ok": 1}

    maybe_add_mtls(app)
    assert TestClient(app).get("/api/v1/h").status_code == 403


def test_build_ssl_context_with_openssl(tmp_path):
    import shutil
    import subprocess

    if shutil.which("openssl") is None:
        return
    key = tmp_path / "k.pem"
    cert = tmp_path / "c.pem"
    subprocess.run(
        [
            "openssl",
            "req",
            "-x509",
            "-newkey",
            "rsa:2048",
            "-nodes",
            "-keyout",
            str(key),
            "-out",
            str(cert),
            "-subj",
            "/CN=test",
            "-days",
            "1",
        ],
        check=True,
        capture_output=True,
    )
    ctx = build_ssl_context(str(cert), str(cert), str(key))
    assert ctx is not None


def test_mtls_client_missing_files(tmp_path):
    try:
        mtls_client("https://x", str(tmp_path / "a"), str(tmp_path / "b"), str(tmp_path / "c"))
    except FileNotFoundError:
        return
    raise AssertionError("expected FileNotFoundError")
