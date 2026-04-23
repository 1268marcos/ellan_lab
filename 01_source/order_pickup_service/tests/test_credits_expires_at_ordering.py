# Unitário: seleção do crédito de checkout por menor expires_at e exclusão de inválidos.

from __future__ import annotations

import os
import tempfile
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.db import Base
from app.models.credit import Credit, CreditStatus
from app.services.credits_service import select_checkout_credit_candidate


def _utc_now():
    return datetime.now(timezone.utc)


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


def test_select_checkout_credit_candidate_picks_earliest_expires_at(engine):
    Session = sessionmaker(bind=engine, future=True)
    db = Session()
    now = _utc_now()
    try:
        # Três créditos elegíveis (pedido 10_000 → max desconto 9_999); vence antes = escolhido.
        rows = [
            Credit(
                id="c-mid",
                user_id="u-sort",
                order_id="orig-mid",
                amount_cents=1000,
                status=CreditStatus.AVAILABLE,
                created_at=now,
                updated_at=now,
                expires_at=now + timedelta(days=15),
                used_at=None,
                revoked_at=None,
            ),
            Credit(
                id="c-early",
                user_id="u-sort",
                order_id="orig-early",
                amount_cents=1000,
                status=CreditStatus.AVAILABLE,
                created_at=now,
                updated_at=now,
                expires_at=now + timedelta(days=3),
                used_at=None,
                revoked_at=None,
            ),
            Credit(
                id="c-late",
                user_id="u-sort",
                order_id="orig-late",
                amount_cents=1000,
                status=CreditStatus.AVAILABLE,
                created_at=now,
                updated_at=now,
                expires_at=now + timedelta(days=40),
                used_at=None,
                revoked_at=None,
            ),
        ]
        for r in rows:
            db.add(r)
        db.commit()

        chosen = select_checkout_credit_candidate(
            db=db,
            user_id="u-sort",
            order_amount_cents=10_000,
            requested_credit_id=None,
            now=now,
            lock_for_update=False,
        )
        assert chosen is not None
        assert chosen.id == "c-early"
    finally:
        db.close()


def test_select_checkout_credit_candidate_skips_expired_and_used(engine):
    Session = sessionmaker(bind=engine, future=True)
    db = Session()
    now = _utc_now()
    try:
        db.add(
            Credit(
                id="c-expired",
                user_id="u-inv",
                order_id="orig-exp",
                amount_cents=500,
                status=CreditStatus.AVAILABLE,
                created_at=now - timedelta(days=10),
                updated_at=now - timedelta(days=10),
                expires_at=now - timedelta(days=1),
                used_at=None,
                revoked_at=None,
            )
        )
        db.add(
            Credit(
                id="c-used",
                user_id="u-inv",
                order_id="orig-used",
                amount_cents=500,
                status=CreditStatus.USED,
                created_at=now,
                updated_at=now,
                expires_at=now + timedelta(days=20),
                used_at=now,
                revoked_at=None,
            )
        )
        db.add(
            Credit(
                id="c-ok",
                user_id="u-inv",
                order_id="orig-ok",
                amount_cents=400,
                status=CreditStatus.AVAILABLE,
                created_at=now,
                updated_at=now,
                expires_at=now + timedelta(days=10),
                used_at=None,
                revoked_at=None,
            )
        )
        db.commit()

        chosen = select_checkout_credit_candidate(
            db=db,
            user_id="u-inv",
            order_amount_cents=5000,
            requested_credit_id=None,
            now=now,
            lock_for_update=False,
        )
        assert chosen is not None
        assert chosen.id == "c-ok"
    finally:
        db.close()
