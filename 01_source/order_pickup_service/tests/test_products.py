from __future__ import annotations

import os
import tempfile
from datetime import datetime, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.auth_dep import get_current_public_user, get_current_user, get_db
from app.routers import products as products_router


class _AdminOpsUser:
    id = "user-products-test-001"
    full_name = "Ops"
    email = "ops-products@example.com"
    is_active = True
    email_verified = True


def _sqlite_products_session():
    fd, path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    engine = create_engine(
        f"sqlite:///{path}",
        future=True,
        connect_args={"check_same_thread": False},
    )
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE products (
                    id VARCHAR(255) PRIMARY KEY NOT NULL,
                    name VARCHAR(500) NOT NULL DEFAULT '',
                    amount_cents INTEGER,
                    category_id VARCHAR(255),
                    status VARCHAR(30),
                    is_active INTEGER NOT NULL DEFAULT 0,
                    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS ops_action_audit (
                    id VARCHAR(40) PRIMARY KEY NOT NULL,
                    action VARCHAR(120) NOT NULL,
                    result VARCHAR(20) NOT NULL,
                    correlation_id VARCHAR(80) NOT NULL,
                    user_id VARCHAR(36),
                    role VARCHAR(80),
                    order_id VARCHAR(36),
                    error_message TEXT,
                    details_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO products (id, name, amount_cents, category_id, status, is_active, updated_at)
                VALUES
                    ('p1', 'Item com preço', 1999, 'cat-a', 'ACTIVE', 1, datetime('now')),
                    ('p2', 'Item sem amount', NULL, NULL, 'DRAFT', 0, datetime('now')),
                    ('p3', 'Inativo', 100, NULL, 'INACTIVE', 0, datetime('now'))
                """
            )
        )
    Session = sessionmaker(bind=engine, future=True)
    return engine, Session, path


def _to_iso_utc_sqlite(value):
    """SQLite devolve updated_at como str; espelha _to_iso_utc do router para testes."""
    if value is None:
        return datetime.now(timezone.utc).isoformat()
    if isinstance(value, str):
        parsed = datetime.fromisoformat(value.replace(" ", "T", 1))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).isoformat()
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


@pytest.fixture()
def products_client(monkeypatch):
    engine, Session, path = _sqlite_products_session()
    monkeypatch.setattr("app.core.auth_dep.user_has_any_role", lambda *args, **kwargs: True)
    monkeypatch.setattr(products_router, "_to_iso_utc", _to_iso_utc_sqlite)

    app = FastAPI()
    app.include_router(products_router.router)

    def override_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_public_user] = lambda: _AdminOpsUser()
    app.dependency_overrides[get_current_user] = lambda: _AdminOpsUser()

    client = TestClient(app)
    yield client
    engine.dispose()
    try:
        os.remove(path)
    except OSError:
        pass


def test_list_products_returns_200_and_items_array(products_client):
    r = products_client.get("/products")
    assert r.status_code == 200
    body = r.json()
    assert body.get("ok") is True
    assert isinstance(body.get("items"), list)
    assert body.get("total") == 3


def test_list_products_amount_cents_present_int_non_negative(products_client):
    r = products_client.get("/products")
    assert r.status_code == 200
    for item in r.json()["items"]:
        assert "amount_cents" in item
        assert isinstance(item["amount_cents"], int)
        assert item["amount_cents"] >= 0


def test_list_products_null_amount_cents_becomes_zero(products_client):
    r = products_client.get("/products")
    assert r.status_code == 200
    by_id = {i["id"]: i for i in r.json()["items"]}
    assert by_id["p1"]["amount_cents"] == 1999
    assert by_id["p2"]["amount_cents"] == 0


def test_patch_product_price_ok_and_audit_row(products_client):
    r = products_client.patch("/products/p1/price", json={"amount_cents": 2500})
    assert r.status_code == 200
    assert r.json() == {"ok": True, "product_id": "p1", "amount_cents": 2500}
    r2 = products_client.get("/products")
    by_id = {i["id"]: i for i in r2.json()["items"]}
    assert by_id["p1"]["amount_cents"] == 2500


def test_patch_product_price_negative_rejected(products_client):
    r = products_client.patch("/products/p1/price", json={"amount_cents": -1})
    assert r.status_code == 422


def test_patch_product_price_inactive_status_rejected(products_client):
    r = products_client.patch("/products/p3/price", json={"amount_cents": 50})
    assert r.status_code == 422
    assert r.json()["detail"]["type"] == "PRODUCT_PRICE_STATUS_NOT_ALLOWED"
