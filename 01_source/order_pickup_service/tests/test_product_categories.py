from __future__ import annotations

import os
import tempfile

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.auth_dep import get_current_public_user, get_db
from app.routers import product_categories as categories_router


class _AdminOpsUser:
    id = "user-categories-test-001"
    full_name = "Ops"
    email = "ops-categories@example.com"
    is_active = True
    email_verified = True


def _sqlite_categories_session():
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
                CREATE TABLE product_categories (
                    id VARCHAR(64) PRIMARY KEY NOT NULL,
                    name VARCHAR(128) NOT NULL,
                    description TEXT,
                    parent_category VARCHAR(64),
                    default_temperature_zone VARCHAR(32) NOT NULL DEFAULT 'AMBIENT',
                    default_security_level VARCHAR(32) NOT NULL DEFAULT 'STANDARD',
                    is_hazardous INTEGER NOT NULL DEFAULT 0,
                    requires_age_verification INTEGER NOT NULL DEFAULT 0,
                    requires_id INTEGER DEFAULT 0,
                    requires_signature INTEGER DEFAULT 0,
                    max_weight_g INTEGER,
                    max_width_mm INTEGER,
                    max_height_mm INTEGER,
                    max_depth_mm INTEGER,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO product_categories (id, name, parent_category, is_hazardous)
                VALUES ('ROOT', 'Raiz', NULL, 0)
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE products (
                    id VARCHAR(255) PRIMARY KEY NOT NULL,
                    category_id VARCHAR(64)
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE product_locker_configs (
                    id VARCHAR(36) PRIMARY KEY NOT NULL,
                    category VARCHAR(64) NOT NULL
                )
                """
            )
        )
    Session = sessionmaker(bind=engine, future=True)
    return engine, Session, path


@pytest.fixture()
def categories_client(monkeypatch):
    engine, Session, path = _sqlite_categories_session()
    monkeypatch.setattr("app.core.auth_dep.user_has_any_role", lambda *args, **kwargs: True)

    app = FastAPI()
    app.include_router(categories_router.router)

    def override_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_public_user] = lambda: _AdminOpsUser()
    client = TestClient(app)
    yield client
    engine.dispose()
    try:
        os.remove(path)
    except OSError:
        pass


def test_list_categories(categories_client):
    r = categories_client.get("/product-categories")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert len(body["items"]) >= 1


def test_create_and_get_category(categories_client):
    r = categories_client.post(
        "/product-categories",
        json={
            "id": "PHARMACY_OTC",
            "name": "Farmácia OTC",
            "parent_category": "ROOT",
            "metadata_json": {"temperature_zone": "AMBIENT", "security_level": "ENHANCED", "is_hazardous": False},
            "requires_age_verification": True,
            "max_weight_g": 5000,
        },
    )
    assert r.status_code == 200
    created = r.json()
    assert created["id"] == "PHARMACY_OTC"
    assert created["requires_age_verification"] is True
    assert created["max_weight_g"] == 5000

    r2 = categories_client.get("/product-categories/PHARMACY_OTC")
    assert r2.status_code == 200
    assert r2.json()["name"] == "Farmácia OTC"


def test_delete_category_with_child_rejected(categories_client):
    categories_client.post(
        "/product-categories",
        json={"id": "CHILD_CAT", "name": "Filha", "parent_category": "ROOT"},
    )
    r = categories_client.delete("/product-categories/ROOT")
    assert r.status_code == 409
    assert r.json()["detail"]["type"] == "CATEGORY_HAS_CHILDREN"
