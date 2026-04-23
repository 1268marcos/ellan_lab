# E2E leve (HTTP via TestClient): rotas /public/me/credits + checkout-preview,
# sem subir app.main (evita init_db / schema completo).

from __future__ import annotations

import os
import tempfile
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.auth_dep import get_current_public_user
from app.core.db import Base, get_db
from app.models.credit import Credit, CreditStatus
from app.routers.public_me import router as public_me_router


class FakeUser:
    id = "user-e2e-light"
    is_active = True
    email_verified = True


@pytest.fixture()
def engine():
    fd, path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    eng = create_engine(
        f"sqlite:///{path}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    Base.metadata.create_all(bind=eng, tables=[Credit.__table__])
    try:
        yield eng
    finally:
        eng.dispose()
        try:
            os.unlink(path)
        except OSError:
            pass


@pytest.fixture()
def api_client(engine):
    Session = sessionmaker(bind=engine, future=True)
    session = Session()
    now = datetime.now(timezone.utc)
    session.add(
        Credit(
            id="cr-later",
            user_id=FakeUser.id,
            order_id="orig-later",
            amount_cents=800,
            status=CreditStatus.AVAILABLE,
            created_at=now,
            updated_at=now,
            expires_at=now + timedelta(days=25),
            used_at=None,
            revoked_at=None,
        )
    )
    session.add(
        Credit(
            id="cr-sooner",
            user_id=FakeUser.id,
            order_id="orig-sooner",
            amount_cents=800,
            status=CreditStatus.AVAILABLE,
            created_at=now,
            updated_at=now,
            expires_at=now + timedelta(days=4),
            used_at=None,
            revoked_at=None,
        )
    )
    session.commit()

    app = FastAPI()
    app.include_router(public_me_router)

    def override_db():
        yield session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_public_user] = lambda: FakeUser()

    client = TestClient(app)
    try:
        yield client
    finally:
        session.close()


def test_e2e_light_list_credits(api_client: TestClient):
    r = api_client.get("/public/me/credits")
    assert r.status_code == 200
    data = r.json()
    assert data["summary"]["available_count"] == 2
    ids = {item["id"] for item in data["items"]}
    assert ids == {"cr-later", "cr-sooner"}


def test_e2e_light_checkout_preview_toggle_use_credit(api_client: TestClient):
    r_off = api_client.get(
        "/public/me/credits/checkout-preview",
        params={"amount_cents": 5000, "use_credit": False, "region": "SP"},
    )
    assert r_off.status_code == 200
    off = r_off.json()
    assert off["eligible"] is False
    assert off["requested_use_credit"] is False
    assert off["final_amount_cents"] == 5000

    r_on = api_client.get(
        "/public/me/credits/checkout-preview",
        params={"amount_cents": 5000, "use_credit": True, "region": "SP"},
    )
    assert r_on.status_code == 200
    on = r_on.json()
    assert on["eligible"] is True
    assert on["credit_id"] == "cr-sooner"
    assert on["discount_cents"] == 800
    assert on["final_amount_cents"] == 4200
