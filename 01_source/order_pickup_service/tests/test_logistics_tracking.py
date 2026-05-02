from __future__ import annotations

import os
import tempfile
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.auth_dep import get_current_public_user, get_db
from app.routers import logistics as logistics_router


class _OpsUser:
    id = "ops-test-user"


def _sqlite_engine():
    fd, path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    engine = create_engine(f"sqlite:///{path}", future=True, connect_args={"check_same_thread": False})
    return engine, path


def _create_return_tracking_schema(conn):
    conn.execute(text("CREATE TABLE inbound_deliveries (id VARCHAR(36) PRIMARY KEY)"))
    conn.execute(
        text(
            """
            CREATE TABLE return_requests (
              id VARCHAR(36) PRIMARY KEY,
              original_delivery_id VARCHAR(36) NOT NULL,
              locker_id VARCHAR(64),
              requester_type VARCHAR(20) NOT NULL,
              requester_id VARCHAR(36),
              return_reason_code VARCHAR(30) NOT NULL,
              return_reason_detail TEXT,
              photo_url VARCHAR(500),
              status VARCHAR(30) NOT NULL,
              requested_at TIMESTAMP NOT NULL,
              approved_at TIMESTAMP,
              approved_by VARCHAR(36),
              closed_at TIMESTAMP,
              close_reason VARCHAR(255),
              created_at TIMESTAMP NOT NULL,
              updated_at TIMESTAMP NOT NULL
            )
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE return_legs (
              id VARCHAR(36) PRIMARY KEY,
              return_request_id VARCHAR(36) NOT NULL,
              logistics_partner_id VARCHAR(36),
              tracking_code VARCHAR(128),
              label_id VARCHAR(36),
              from_locker_id VARCHAR(64),
              to_hub_address_json TEXT,
              status VARCHAR(20) NOT NULL,
              shipped_at TIMESTAMP,
              received_at TIMESTAMP,
              created_at TIMESTAMP NOT NULL,
              updated_at TIMESTAMP NOT NULL
            )
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE return_tracking_events (
              id VARCHAR(36) PRIMARY KEY,
              return_leg_id VARCHAR(36) NOT NULL,
              event_code VARCHAR(30) NOT NULL,
              description VARCHAR(255),
              location_name VARCHAR(128),
              occurred_at TIMESTAMP NOT NULL,
              source VARCHAR(20) NOT NULL,
              created_at TIMESTAMP NOT NULL
            )
            """
        )
    )


@pytest.fixture()
def logistics_tracking_client(monkeypatch):
    monkeypatch.setattr("app.core.auth_dep.user_has_any_role", lambda *args, **kwargs: True)
    engine, path = _sqlite_engine()
    with engine.begin() as conn:
        _create_return_tracking_schema(conn)
    Session = sessionmaker(bind=engine, future=True)
    app = FastAPI()
    app.include_router(logistics_router.router)

    def override_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_public_user] = lambda: _OpsUser()
    client = TestClient(app)
    try:
        yield client, Session
    finally:
        engine.dispose()
        try:
            os.unlink(path)
        except OSError:
            pass


def test_get_tracking_events_success(logistics_tracking_client):
    client, Session = logistics_tracking_client
    delivery_id = str(uuid4())
    rr_id = str(uuid4())
    leg_id = str(uuid4())
    ev_old = str(uuid4())
    ev_new = str(uuid4())
    now = datetime.now(timezone.utc)
    t_old = now - timedelta(hours=2)
    t_new = now - timedelta(hours=1)
    db = Session()
    try:
        db.execute(text("INSERT INTO inbound_deliveries (id) VALUES (:id)"), {"id": delivery_id})
        db.execute(
            text(
                """
                INSERT INTO return_requests (
                  id, original_delivery_id, locker_id, requester_type, requester_id,
                  return_reason_code, return_reason_detail, photo_url, status,
                  requested_at, approved_at, approved_by, closed_at, close_reason,
                  created_at, updated_at
                ) VALUES (
                  :id, :delivery_id, NULL, 'OPS', NULL,
                  'DAMAGED_ITEM', NULL, NULL, 'IN_TRANSIT',
                  :requested_at, NULL, NULL, NULL, NULL,
                  :created_at, :updated_at
                )
                """
            ),
            {
                "id": rr_id,
                "delivery_id": delivery_id,
                "requested_at": t_old,
                "created_at": t_old,
                "updated_at": now,
            },
        )
        db.execute(
            text(
                """
                INSERT INTO return_legs (
                  id, return_request_id, logistics_partner_id, tracking_code, label_id,
                  from_locker_id, to_hub_address_json, status, shipped_at, received_at,
                  created_at, updated_at
                ) VALUES (
                  :id, :rr_id, NULL, 'TRK-1', NULL,
                  NULL, '{}', 'IN_TRANSIT', NULL, NULL,
                  :created_at, :updated_at
                )
                """
            ),
            {"id": leg_id, "rr_id": rr_id, "created_at": now, "updated_at": now},
        )
        db.execute(
            text(
                """
                INSERT INTO return_tracking_events (
                  id, return_leg_id, event_code, description, location_name,
                  occurred_at, source, created_at
                ) VALUES (
                  :id, :leg_id, 'PICKUP_DONE', 'Coletado', 'Hub SP',
                  :occurred_at, 'CARRIER_WEBHOOK', :created_at
                )
                """
            ),
            {"id": ev_old, "leg_id": leg_id, "occurred_at": t_old, "created_at": t_old},
        )
        db.execute(
            text(
                """
                INSERT INTO return_tracking_events (
                  id, return_leg_id, event_code, description, location_name,
                  occurred_at, source, created_at
                ) VALUES (
                  :id, :leg_id, 'IN_TRANSIT', NULL, NULL,
                  :occurred_at, 'OPS', :created_at
                )
                """
            ),
            {"id": ev_new, "leg_id": leg_id, "occurred_at": t_new, "created_at": t_new},
        )
        db.commit()
    finally:
        db.close()

    r = client.get(f"/logistics/return-legs/{leg_id}/tracking-events")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 2
    assert body["limit"] == 50
    assert body["offset"] == 0
    assert len(body["items"]) == 2
    assert body["items"][0]["event_code"] == "IN_TRANSIT"
    assert body["items"][1]["event_code"] == "PICKUP_DONE"


def test_get_tracking_events_empty(logistics_tracking_client):
    client, Session = logistics_tracking_client
    delivery_id = str(uuid4())
    rr_id = str(uuid4())
    leg_id = str(uuid4())
    now = datetime.now(timezone.utc)
    db = Session()
    try:
        db.execute(text("INSERT INTO inbound_deliveries (id) VALUES (:id)"), {"id": delivery_id})
        db.execute(
            text(
                """
                INSERT INTO return_requests (
                  id, original_delivery_id, locker_id, requester_type, requester_id,
                  return_reason_code, return_reason_detail, photo_url, status,
                  requested_at, approved_at, approved_by, closed_at, close_reason,
                  created_at, updated_at
                ) VALUES (
                  :id, :delivery_id, NULL, 'OPS', NULL,
                  'OTHER', NULL, NULL, 'REQUESTED',
                  :requested_at, NULL, NULL, NULL, NULL,
                  :created_at, :updated_at
                )
                """
            ),
            {
                "id": rr_id,
                "delivery_id": delivery_id,
                "requested_at": now,
                "created_at": now,
                "updated_at": now,
            },
        )
        db.execute(
            text(
                """
                INSERT INTO return_legs (
                  id, return_request_id, logistics_partner_id, tracking_code, label_id,
                  from_locker_id, to_hub_address_json, status, shipped_at, received_at,
                  created_at, updated_at
                ) VALUES (
                  :id, :rr_id, NULL, NULL, NULL,
                  NULL, '{}', 'PENDING', NULL, NULL,
                  :created_at, :updated_at
                )
                """
            ),
            {"id": leg_id, "rr_id": rr_id, "created_at": now, "updated_at": now},
        )
        db.commit()
    finally:
        db.close()

    r = client.get(f"/logistics/return-legs/{leg_id}/tracking-events")
    assert r.status_code == 200
    body = r.json()
    assert body["items"] == []
    assert body["total"] == 0


def test_get_tracking_events_invalid_leg_id(logistics_tracking_client):
    client, _ = logistics_tracking_client
    missing = str(uuid4())
    r = client.get(f"/logistics/return-legs/{missing}/tracking-events")
    assert r.status_code == 404
    assert r.json()["detail"]["type"] == "RETURN_LEG_NOT_FOUND"
