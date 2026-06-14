from __future__ import annotations

import os
import tempfile
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.db import Base
from app.models.credit import Credit, CreditStatus
from app.services.wallet_credits import (
    apply_credit_for_checkout,
    resolve_credit_currency,
    select_checkout_credit_candidate,
    summarize_credits_by_currency,
)


class FakeUser:
    id = "user-currency"
    is_active = True
    email_verified = True


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _credit(
    *,
    cid: str,
    amount: int,
    currency: str,
    expires_days: int = 20,
) -> Credit:
    now = _utc_now()
    return Credit(
        id=cid,
        user_id=FakeUser.id,
        order_id=f"order-{cid}",
        amount=amount,
        remaining=amount,
        promotional=True,
        status=CreditStatus.AVAILABLE,
        created_at=now,
        updated_at=now,
        expires_at=now + timedelta(days=expires_days),
        used_at=None,
        revoked_at=None,
        metadata_json={"currency": currency, "type": "PICKUP_EXPIRATION"},
    )


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


def test_summarize_credits_groups_by_currency(engine):
    Session = sessionmaker(bind=engine, future=True)
    db = Session()
    now = _utc_now()
    try:
        db.add(_credit(cid="brl-1", amount=1000, currency="BRL"))
        db.add(_credit(cid="eur-1", amount=2500, currency="EUR"))
        db.commit()

        credits = db.query(Credit).all()
        summary = summarize_credits_by_currency(
            credits,
            order_currencies={},
            wallet_currency="BRL",
            now=now,
        )

        assert summary.balances_by_currency == {"BRL": 1000, "EUR": 2500}
        assert summary.available_by_currency == {"BRL": 1000, "EUR": 2500}
        assert summary.display_currency == "BRL"
        assert summary.display_available_balance_cents == 1000
        assert summary.display_available_count == 1
    finally:
        db.close()


def test_select_checkout_credit_candidate_filters_by_order_currency(engine):
    Session = sessionmaker(bind=engine, future=True)
    db = Session()
    now = _utc_now()
    try:
        db.add(_credit(cid="brl", amount=800, currency="BRL", expires_days=5))
        db.add(_credit(cid="eur", amount=800, currency="EUR", expires_days=3))
        db.commit()

        chosen_brl = select_checkout_credit_candidate(
            db=db,
            user_id=FakeUser.id,
            order_amount_cents=5000,
            order_currency="BRL",
            wallet_currency="BRL",
            now=now,
            lock_for_update=False,
        )
        assert chosen_brl is not None
        assert chosen_brl.id == "brl"

        chosen_eur = select_checkout_credit_candidate(
            db=db,
            user_id=FakeUser.id,
            order_amount_cents=5000,
            order_currency="EUR",
            wallet_currency="BRL",
            now=now,
            lock_for_update=False,
        )
        assert chosen_eur is not None
        assert chosen_eur.id == "eur"
    finally:
        db.close()


def test_apply_credit_for_checkout_rejects_wallet_order_currency_mismatch(engine):
    Session = sessionmaker(bind=engine, future=True)
    db = Session()
    try:
        db.add(_credit(cid="brl-only", amount=800, currency="BRL"))
        db.commit()

        with patch(
            "app.services.wallet_credits.get_user_wallet_currency",
            return_value="BRL",
        ):
            result = apply_credit_for_checkout(
                db=db,
                user_id=FakeUser.id,
                base_amount_cents=5000,
                order_currency="EUR",
                use_credit=True,
            )
        assert result.applied is False
        assert result.reason == "currency_mismatch"
    finally:
        db.close()


def test_resolve_credit_currency_prefers_metadata():
    credit = Credit(
        id="x",
        user_id="u",
        amount=100,
        remaining=100,
        promotional=False,
        status=CreditStatus.AVAILABLE,
        metadata_json={"currency": "EUR"},
    )
    assert resolve_credit_currency(credit, order_currency="BRL", wallet_currency="BRL") == "EUR"
