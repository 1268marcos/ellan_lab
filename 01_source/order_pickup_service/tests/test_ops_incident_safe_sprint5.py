from __future__ import annotations

import os
import tempfile

import pytest
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


@pytest.mark.parametrize(
    ("method", "path", "payload"),
    [
        ("post", "/dev-admin/reconcile-order", {"order_id": "order-should-not-run"}),
        ("post", "/dev-admin/reconciliation-pending/run-once", None),
        ("get", "/dev-admin/reconciliation-pending", None),
        ("get", "/dev-admin/ops-audit", None),
        ("get", "/dev-admin/ops-metrics", None),
    ],
)
def test_dev_admin_role_required_error_contract_is_consistent(method, path, payload):
    engine, Session, db_path = _prepare_db()
    try:
        client = _build_client(Session)
        response = client.request(method.upper(), path, json=payload)
        assert response.status_code == 403
        body = response.json()
        detail = body.get("detail", {})
        assert detail.get("type") == "ROLE_REQUIRED"
        assert isinstance(detail.get("message"), str)
        assert detail.get("message")
        assert detail.get("allowed_roles") == ["admin_operacao", "auditoria"]
    finally:
        engine.dispose()
        try:
            os.unlink(db_path)
        except OSError:
            pass


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


def test_dev_admin_reconciliation_pending_list_denies_without_role_and_no_side_effect(monkeypatch):
    engine, Session, db_path = _prepare_db()
    try:
        client = _build_client(Session)
        touched = {"pending_list_called": False, "audit_write_called": False}

        def _unexpected_pending_list(*args, **kwargs):
            touched["pending_list_called"] = True
            raise AssertionError("list_reconciliation_pending should not be called for no-role user")

        def _unexpected_audit_write(*args, **kwargs):
            touched["audit_write_called"] = True
            raise AssertionError("_safe_record_ops_audit should not be called for no-role user")

        monkeypatch.setattr(
            "app.routers.dev_admin.list_reconciliation_pending",
            _unexpected_pending_list,
        )
        monkeypatch.setattr(
            "app.routers.dev_admin._safe_record_ops_audit",
            _unexpected_audit_write,
        )

        response = client.get("/dev-admin/reconciliation-pending")
        assert response.status_code == 403
        body = response.json()
        assert body.get("detail", {}).get("type") == "ROLE_REQUIRED"
        assert touched["pending_list_called"] is False
        assert touched["audit_write_called"] is False
    finally:
        engine.dispose()
        try:
            os.unlink(db_path)
        except OSError:
            pass


def test_dev_admin_release_regional_allocations_denies_without_role_and_no_side_effect(monkeypatch):
    engine, Session, db_path = _prepare_db()
    try:
        client = _build_client(Session)
        touched = {"dev_mode_guard_called": False, "locker_registry_called": False}

        def _unexpected_dev_mode_guard(*args, **kwargs):
            touched["dev_mode_guard_called"] = True
            raise AssertionError("_ensure_dev_mode should not be called for no-role user")

        def _unexpected_locker_registry_call(*args, **kwargs):
            touched["locker_registry_called"] = True
            raise AssertionError("backend_client.get_locker_registry_item should not be called for no-role user")

        monkeypatch.setattr(
            "app.routers.dev_admin._ensure_dev_mode",
            _unexpected_dev_mode_guard,
        )
        monkeypatch.setattr(
            "app.routers.dev_admin.backend_client.get_locker_registry_item",
            _unexpected_locker_registry_call,
        )

        response = client.post(
            "/dev-admin/release-regional-allocations",
            json={"region": "SP", "locker_id": "LOCKER-01"},
        )
        assert response.status_code == 403
        body = response.json()
        assert body.get("detail", {}).get("type") == "ROLE_REQUIRED"
        assert touched["dev_mode_guard_called"] is False
        assert touched["locker_registry_called"] is False
    finally:
        engine.dispose()
        try:
            os.unlink(db_path)
        except OSError:
            pass


def test_dev_admin_reset_locker_denies_without_role_and_no_side_effect(monkeypatch):
    engine, Session, db_path = _prepare_db()
    try:
        client = _build_client(Session)
        touched = {"dev_mode_guard_called": False, "locker_registry_called": False}

        def _unexpected_dev_mode_guard(*args, **kwargs):
            touched["dev_mode_guard_called"] = True
            raise AssertionError("_ensure_dev_mode should not be called for no-role user")

        def _unexpected_locker_registry_call(*args, **kwargs):
            touched["locker_registry_called"] = True
            raise AssertionError("backend_client.get_locker_registry_item should not be called for no-role user")

        monkeypatch.setattr(
            "app.routers.dev_admin._ensure_dev_mode",
            _unexpected_dev_mode_guard,
        )
        monkeypatch.setattr(
            "app.routers.dev_admin.backend_client.get_locker_registry_item",
            _unexpected_locker_registry_call,
        )

        response = client.post(
            "/dev-admin/reset-locker",
            json={"region": "SP", "locker_id": "LOCKER-01"},
        )
        assert response.status_code == 403
        body = response.json()
        assert body.get("detail", {}).get("type") == "ROLE_REQUIRED"
        assert touched["dev_mode_guard_called"] is False
        assert touched["locker_registry_called"] is False
    finally:
        engine.dispose()
        try:
            os.unlink(db_path)
        except OSError:
            pass


def test_dev_admin_simulate_online_payment_legacy_not_use_denies_without_role_and_no_side_effect(
    monkeypatch,
):
    engine, Session, db_path = _prepare_db()
    try:
        client = _build_client(Session)
        touched = {"dev_mode_guard_called": False}

        def _unexpected_dev_mode_guard(*args, **kwargs):
            touched["dev_mode_guard_called"] = True
            raise AssertionError("_ensure_dev_mode should not be called for no-role user")

        monkeypatch.setattr(
            "app.routers.dev_admin._ensure_dev_mode",
            _unexpected_dev_mode_guard,
        )

        response = client.post(
            "/dev-admin/simulate-online-payment-legacy-not-use",
            params={"order_id": "order-should-not-run"},
        )
        assert response.status_code == 403
        body = response.json()
        assert body.get("detail", {}).get("type") == "ROLE_REQUIRED"
        assert touched["dev_mode_guard_called"] is False
    finally:
        engine.dispose()
        try:
            os.unlink(db_path)
        except OSError:
            pass


def test_dev_admin_simulate_online_payment_denies_without_role_and_no_side_effect(monkeypatch):
    engine, Session, db_path = _prepare_db()
    try:
        client = _build_client(Session)
        touched = {
            "dev_mode_guard_called": False,
            "ensure_allocation_called": False,
            "ensure_online_pickup_called": False,
            "create_pickup_token_called": False,
            "fulfillment_called": False,
        }

        def _unexpected_dev_mode_guard(*args, **kwargs):
            touched["dev_mode_guard_called"] = True
            raise AssertionError("_ensure_dev_mode should not be called for no-role user")

        def _unexpected_ensure_allocation(*args, **kwargs):
            touched["ensure_allocation_called"] = True
            raise AssertionError("_ensure_allocation should not be called for no-role user")

        def _unexpected_ensure_online_pickup(*args, **kwargs):
            touched["ensure_online_pickup_called"] = True
            raise AssertionError("_ensure_online_pickup should not be called for no-role user")

        def _unexpected_create_pickup_token(*args, **kwargs):
            touched["create_pickup_token_called"] = True
            raise AssertionError("_create_pickup_token should not be called for no-role user")

        def _unexpected_fulfillment(*args, **kwargs):
            touched["fulfillment_called"] = True
            raise AssertionError("fulfill_payment_post_approval should not be called for no-role user")

        monkeypatch.setattr(
            "app.routers.dev_admin._ensure_dev_mode",
            _unexpected_dev_mode_guard,
        )
        monkeypatch.setattr(
            "app.routers.dev_admin._ensure_allocation",
            _unexpected_ensure_allocation,
        )
        monkeypatch.setattr(
            "app.routers.dev_admin._ensure_online_pickup",
            _unexpected_ensure_online_pickup,
        )
        monkeypatch.setattr(
            "app.routers.dev_admin._create_pickup_token",
            _unexpected_create_pickup_token,
        )
        monkeypatch.setattr(
            "app.routers.dev_admin.fulfill_payment_post_approval",
            _unexpected_fulfillment,
        )

        response = client.post(
            "/dev-admin/simulate-online-payment",
            params={"order_id": "order-should-not-run"},
        )
        assert response.status_code == 403
        body = response.json()
        assert body.get("detail", {}).get("type") == "ROLE_REQUIRED"
        assert touched["dev_mode_guard_called"] is False
        assert touched["ensure_allocation_called"] is False
        assert touched["ensure_online_pickup_called"] is False
        assert touched["create_pickup_token_called"] is False
        assert touched["fulfillment_called"] is False
    finally:
        engine.dispose()
        try:
            os.unlink(db_path)
        except OSError:
            pass


def test_dev_admin_reconcile_order_denies_without_role_and_no_audit_write(monkeypatch):
    engine, Session, db_path = _prepare_db()
    try:
        client = _build_client(Session)
        touched = {"reconcile_called": False, "audit_write_called": False}

        def _unexpected_reconcile_call(*args, **kwargs):
            touched["reconcile_called"] = True
            raise AssertionError("reconcile_order_compensation should not be called for no-role user")

        def _unexpected_audit_write(*args, **kwargs):
            touched["audit_write_called"] = True
            raise AssertionError("_safe_record_ops_audit should not be called for no-role user")

        monkeypatch.setattr(
            "app.routers.dev_admin.reconcile_order_compensation",
            _unexpected_reconcile_call,
        )
        monkeypatch.setattr(
            "app.routers.dev_admin._safe_record_ops_audit",
            _unexpected_audit_write,
        )

        response = client.post(
            "/dev-admin/reconcile-order",
            json={"order_id": "order-should-not-run"},
        )
        assert response.status_code == 403
        body = response.json()
        assert body.get("detail", {}).get("type") == "ROLE_REQUIRED"
        assert touched["reconcile_called"] is False
        assert touched["audit_write_called"] is False
    finally:
        engine.dispose()
        try:
            os.unlink(db_path)
        except OSError:
            pass


def test_dev_admin_pending_run_once_denies_without_role_and_no_audit_write(monkeypatch):
    engine, Session, db_path = _prepare_db()
    try:
        client = _build_client(Session)
        touched = {"run_once_called": False, "audit_write_called": False}

        def _unexpected_run_once_call(*args, **kwargs):
            touched["run_once_called"] = True
            raise AssertionError("run_reconciliation_retry_once should not be called for no-role user")

        def _unexpected_audit_write(*args, **kwargs):
            touched["audit_write_called"] = True
            raise AssertionError("_safe_record_ops_audit should not be called for no-role user")

        monkeypatch.setattr(
            "app.routers.dev_admin.run_reconciliation_retry_once",
            _unexpected_run_once_call,
        )
        monkeypatch.setattr(
            "app.routers.dev_admin._safe_record_ops_audit",
            _unexpected_audit_write,
        )

        response = client.post("/dev-admin/reconciliation-pending/run-once")
        assert response.status_code == 403
        body = response.json()
        assert body.get("detail", {}).get("type") == "ROLE_REQUIRED"
        assert touched["run_once_called"] is False
        assert touched["audit_write_called"] is False
    finally:
        engine.dispose()
        try:
            os.unlink(db_path)
        except OSError:
            pass
