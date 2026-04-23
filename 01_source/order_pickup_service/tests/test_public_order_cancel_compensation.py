from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.auth_dep import get_current_user
from app.core.db import Base, get_db
from app.models.allocation import Allocation, AllocationState
from app.models.credit import Credit, CreditStatus
from app.models.order import Order, OrderChannel, OrderStatus, PaymentMethod, PaymentStatus
from app.models.pickup import Pickup, PickupChannel, PickupLifecycleStage, PickupStatus
from app.routers.public_orders import router as public_orders_router


class _FakeUser:
    id = "user-cancel-comp"


@pytest.fixture()
def client_and_sessionmaker():
    db_url = str(os.getenv("ORDER_PICKUP_TEST_DATABASE_URL") or "").strip()
    if not db_url:
        pytest.skip("ORDER_PICKUP_TEST_DATABASE_URL não definido para teste de compensação de cancelamento.")

    engine = create_engine(
        db_url,
        future=True,
    )
    Base.metadata.create_all(
        bind=engine,
        tables=[
            Order.__table__,
            Allocation.__table__,
            Credit.__table__,
            Pickup.__table__,
        ],
    )
    SessionLocal = sessionmaker(bind=engine, future=True)

    app = FastAPI()
    app.include_router(public_orders_router)

    def override_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def override_user():
        return _FakeUser()

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_user

    client = TestClient(app)
    try:
        yield client, SessionLocal
    finally:
        engine.dispose()


def _seed_order_allocation_credit(SessionLocal, *, order_status: OrderStatus):
    now = datetime.now(timezone.utc)
    suffix = uuid4().hex[:12]
    order_id = f"order-cancel-comp-{suffix}"
    credit_id = f"credit-cancel-comp-{suffix}"
    allocation_id = f"alloc-cancel-comp-{suffix}"
    pickup_id = f"pickup-cancel-comp-{suffix}"
    db = SessionLocal()
    try:
        order = Order(
            id=order_id,
            user_id=_FakeUser.id,
            channel=OrderChannel.ONLINE,
            region="PT",
            totem_id="PT-GUIMARAES-AZUREM-LK-001",
            sku_id="cookie_especial",
            amount_cents=2641,
            status=order_status,
            payment_method=PaymentMethod.apple_pay,
            payment_status=PaymentStatus.CREATED,
            created_at=now,
            updated_at=now,
            order_metadata={
                "credit_application": {
                    "requested": True,
                    "applied": True,
                    "reason": "applied",
                    "credit_id": credit_id,
                    "discount_cents": 2248,
                    "base_amount_cents": 4889,
                    "final_amount_cents": 2641,
                    "currency": "EUR",
                }
            },
        )
        db.add(order)
        db.flush()

        credit = Credit(
            id=credit_id,
            user_id=_FakeUser.id,
            order_id=order.id,
            amount_cents=2248,
            status=CreditStatus.USED,
            created_at=now,
            updated_at=now,
            expires_at=now + timedelta(days=30),
            used_at=now,
            revoked_at=None,
            source_type="PICKUP_EXPIRATION",
            source_reason="pickup_not_redeemed_before_deadline",
            notes="Aplicado no checkout.",
        )
        db.add(credit)

        allocation = Allocation(
            id=allocation_id,
            order_id=order.id,
            locker_id=order.totem_id,
            slot=19,
            state=AllocationState.RESERVED_PENDING_PAYMENT,
            ttl_seconds=600,
            created_at=now,
            updated_at=now,
        )
        db.add(allocation)

        pickup = Pickup(
            id=pickup_id,
            order_id=order.id,
            channel=PickupChannel.ONLINE,
            region=order.region,
            locker_id=order.totem_id,
            machine_id=order.totem_id,
            slot=19,
            status=PickupStatus.ACTIVE,
            lifecycle_stage=PickupLifecycleStage.READY_FOR_PICKUP,
            activated_at=now,
            ready_at=now,
            created_at=now,
            updated_at=now,
        )
        db.add(pickup)
        db.commit()
        return {
            "order_id": order_id,
            "credit_id": credit_id,
            "allocation_id": allocation_id,
            "pickup_id": pickup_id,
        }
    finally:
        db.close()


def test_cancel_order_restores_credit_and_releases_slot(client_and_sessionmaker, monkeypatch):
    client, SessionLocal = client_and_sessionmaker
    seeded = _seed_order_allocation_credit(SessionLocal, order_status=OrderStatus.PAYMENT_PENDING)

    monkeypatch.setattr(
        "app.routers.public_orders.backend_client.locker_release",
        lambda *args, **kwargs: {"ok": True},
    )

    response = client.post(
        f"/public/orders/{seeded['order_id']}/cancel",
        headers={"X-Device-Fingerprint": "fp-cancel-comp"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "CANCELLED"
    assert body["compensation"]["credit_restored"] is True
    assert body["compensation"]["slot_release_ok"] is True

    db = SessionLocal()
    try:
        credit = db.query(Credit).filter(Credit.id == seeded["credit_id"]).first()
        allocation = db.query(Allocation).filter(Allocation.id == seeded["allocation_id"]).first()
        pickup = db.query(Pickup).filter(Pickup.id == seeded["pickup_id"]).first()

        assert credit is not None
        assert credit.status == CreditStatus.AVAILABLE
        assert credit.used_at is None
        assert allocation is not None
        assert allocation.state == AllocationState.RELEASED
        assert pickup is not None
        assert pickup.status == PickupStatus.CANCELLED
    finally:
        db.close()


def test_cancel_already_cancelled_order_runs_reconciliation(client_and_sessionmaker, monkeypatch):
    client, SessionLocal = client_and_sessionmaker
    seeded = _seed_order_allocation_credit(SessionLocal, order_status=OrderStatus.CANCELLED)

    monkeypatch.setattr(
        "app.routers.public_orders.backend_client.locker_release",
        lambda *args, **kwargs: {"ok": True},
    )

    response = client.post(
        f"/public/orders/{seeded['order_id']}/cancel",
        headers={"X-Device-Fingerprint": "fp-cancel-comp"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "CANCELLED"
    assert body["compensation"]["credit_restored"] is True
    assert body["compensation"]["slot_release_ok"] is True


def test_cancel_expired_credit_50_order_runs_reconciliation(client_and_sessionmaker, monkeypatch):
    client, SessionLocal = client_and_sessionmaker
    seeded = _seed_order_allocation_credit(SessionLocal, order_status=OrderStatus.EXPIRED_CREDIT_50)

    monkeypatch.setattr(
        "app.routers.public_orders.backend_client.locker_release",
        lambda *args, **kwargs: {"ok": True},
    )

    response = client.post(
        f"/public/orders/{seeded['order_id']}/cancel",
        headers={"X-Device-Fingerprint": "fp-cancel-comp"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "CANCELLED"
    assert body["compensation"]["credit_restored"] is True
    assert body["compensation"]["slot_release_ok"] is True


def test_cancel_order_reconciliation_is_idempotent_for_same_order_id(
    client_and_sessionmaker, monkeypatch
):
    client, SessionLocal = client_and_sessionmaker
    seeded = _seed_order_allocation_credit(SessionLocal, order_status=OrderStatus.PAYMENT_PENDING)

    release_calls = {"count": 0}

    def _release_ok(*args, **kwargs):
        release_calls["count"] += 1
        return {"ok": True}

    monkeypatch.setattr(
        "app.routers.public_orders.backend_client.locker_release",
        _release_ok,
    )

    first = client.post(
        f"/public/orders/{seeded['order_id']}/cancel",
        headers={"X-Device-Fingerprint": "fp-cancel-comp"},
    )
    second = client.post(
        f"/public/orders/{seeded['order_id']}/cancel",
        headers={"X-Device-Fingerprint": "fp-cancel-comp"},
    )

    assert first.status_code == 200
    assert second.status_code == 200

    first_body = first.json()
    second_body = second.json()
    assert first_body["status"] == "CANCELLED"
    assert second_body["status"] == "CANCELLED"
    assert first_body["compensation"]["credit_restored"] is True
    assert second_body["compensation"]["credit_restored"] is False

    db = SessionLocal()
    try:
        order = db.query(Order).filter(Order.id == seeded["order_id"]).first()
        credit = db.query(Credit).filter(Credit.id == seeded["credit_id"]).first()
        allocation = db.query(Allocation).filter(Allocation.id == seeded["allocation_id"]).first()
        pickup = db.query(Pickup).filter(Pickup.id == seeded["pickup_id"]).first()
        credit_rows_for_order = db.query(Credit).filter(Credit.order_id == seeded["order_id"]).count()

        assert order is not None
        assert order.status == OrderStatus.CANCELLED
        assert credit is not None
        assert credit.status == CreditStatus.AVAILABLE
        assert credit.used_at is None
        assert credit_rows_for_order == 1
        notes = str(credit.notes or "")
        assert notes.count("Crédito reaberto após compensação de pedido") == 1
        assert allocation is not None
        assert allocation.state == AllocationState.RELEASED
        assert pickup is not None
        assert pickup.status == PickupStatus.CANCELLED
        assert release_calls["count"] == 2
    finally:
        db.close()
