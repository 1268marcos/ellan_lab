from __future__ import annotations

import os
import tempfile

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.auth_dep import get_current_public_user, get_current_user
from app.core.db import get_db
from app.routers.dev_admin import router as dev_admin_router


class _NoRoleUser:
    id = "user-no-role-sprint5"
    full_name = "No Role"
    email = "nobody@example.com"
    phone = None
    is_active = True
    email_verified = True
    phone_verified = False


def _prepare_db():
    fd, path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    engine = create_engine(
        f"sqlite:///{path}",
        future=True,
        connect_args={"check_same_thread": False},
    )
    Session = sessionmaker(bind=engine, future=True)
    return engine, Session, path


def _build_client(Session):
    app = FastAPI()
    app.include_router(dev_admin_router)

    def override_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_public_user] = lambda: _NoRoleUser()
    app.dependency_overrides[get_current_user] = lambda: _NoRoleUser()
    return TestClient(app)


def test_dev_admin_reconcile_order_denies_without_role_and_no_side_effect(monkeypatch):
    engine, Session, db_path = _prepare_db()
    try:
        client = _build_client(Session)
        touched = {"called": False}

        def _unexpected_call(*args, **kwargs):
            touched["called"] = True
            raise AssertionError("reconcile_order_compensation should not be called for no-role user")

        monkeypatch.setattr(
            "app.routers.dev_admin.reconcile_order_compensation",
            _unexpected_call,
        )

        response = client.post(
            "/dev-admin/reconcile-order",
            json={"order_id": "order-should-not-run"},
        )
        assert response.status_code == 403
        body = response.json()
        assert body.get("detail", {}).get("type") == "ROLE_REQUIRED"
        assert touched["called"] is False
    finally:
        engine.dispose()
        try:
            os.unlink(db_path)
        except OSError:
            pass


def test_dev_admin_pending_run_once_denies_without_role_and_no_side_effect(monkeypatch):
    engine, Session, db_path = _prepare_db()
    try:
        client = _build_client(Session)
        touched = {"called": False}

        def _unexpected_call(*args, **kwargs):
            touched["called"] = True
            raise AssertionError("run_reconciliation_retry_once should not be called for no-role user")

        monkeypatch.setattr(
            "app.routers.dev_admin.run_reconciliation_retry_once",
            _unexpected_call,
        )

        response = client.post("/dev-admin/reconciliation-pending/run-once")
        assert response.status_code == 403
        body = response.json()
        assert body.get("detail", {}).get("type") == "ROLE_REQUIRED"
        assert touched["called"] is False
    finally:
        engine.dispose()
        try:
            os.unlink(db_path)
        except OSError:
            pass


def test_dev_admin_ops_metrics_denies_without_role_and_no_side_effect(monkeypatch):
    engine, Session, db_path = _prepare_db()
    try:
        client = _build_client(Session)
        touched = {"metrics_called": False, "audit_called": False}

        def _unexpected_metrics_call(*args, **kwargs):
            touched["metrics_called"] = True
            raise AssertionError("build_ops_metrics should not be called for no-role user")

        def _unexpected_audit_call(*args, **kwargs):
            touched["audit_called"] = True
            raise AssertionError("_safe_record_ops_audit should not be called for no-role user")

        monkeypatch.setattr(
            "app.routers.dev_admin.build_ops_metrics",
            _unexpected_metrics_call,
        )
        monkeypatch.setattr(
            "app.routers.dev_admin._safe_record_ops_audit",
            _unexpected_audit_call,
        )

        response = client.get("/dev-admin/ops-metrics")
        assert response.status_code == 403
        body = response.json()
        assert body.get("detail", {}).get("type") == "ROLE_REQUIRED"
        assert touched["metrics_called"] is False
        assert touched["audit_called"] is False
    finally:
        engine.dispose()
        try:
            os.unlink(db_path)
        except OSError:
            pass


def test_dev_admin_ops_audit_denies_without_role_and_no_side_effect(monkeypatch):
    engine, Session, db_path = _prepare_db()
    try:
        client = _build_client(Session)
        touched = {"audit_list_called": False, "audit_write_called": False}

        def _unexpected_list_call(*args, **kwargs):
            touched["audit_list_called"] = True
            raise AssertionError("list_ops_action_audit should not be called for no-role user")

        def _unexpected_audit_write(*args, **kwargs):
            touched["audit_write_called"] = True
            raise AssertionError("_safe_record_ops_audit should not be called for no-role user")

        monkeypatch.setattr(
            "app.routers.dev_admin.list_ops_action_audit",
            _unexpected_list_call,
        )
        monkeypatch.setattr(
            "app.routers.dev_admin._safe_record_ops_audit",
            _unexpected_audit_write,
        )

        response = client.get("/dev-admin/ops-audit")
        assert response.status_code == 403
        body = response.json()
        assert body.get("detail", {}).get("type") == "ROLE_REQUIRED"
        assert touched["audit_list_called"] is False
        assert touched["audit_write_called"] is False
    finally:
        engine.dispose()
        try:
            os.unlink(db_path)
        except OSError:
            pass
