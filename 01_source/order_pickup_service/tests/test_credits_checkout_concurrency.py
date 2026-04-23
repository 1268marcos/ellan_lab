# Testes de integração para evitar reuso duplo de crédito no checkout.
#
# - SQLite (arquivo): mesma sessão + restauração após compensação.
# - Postgres: concorrência real (ORDER_PICKUP_TEST_DATABASE_URL no CI).

from __future__ import annotations

import os
import tempfile
import threading
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.db import Base
from app.models.credit import Credit, CreditStatus
from app.services.credits_service import (
    apply_credit_for_checkout,
    restore_credit_after_failed_order_creation,
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@pytest.fixture()
def credit_db_path():
    fd, path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    yield path
    try:
        os.unlink(path)
    except OSError:
        pass


@pytest.fixture()
def engine(credit_db_path):
    eng = create_engine(
        f"sqlite:///{credit_db_path}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    Base.metadata.create_all(bind=eng, tables=[Credit.__table__])
    try:
        yield eng
    finally:
        eng.dispose()


def _insert_available_credit(session, *, credit_id: str, user_id: str, amount_cents: int = 500):
    now = _utc_now()
    session.add(
        Credit(
            id=credit_id,
            user_id=user_id,
            order_id=f"orig-{credit_id}",
            amount_cents=amount_cents,
            status=CreditStatus.AVAILABLE,
            created_at=now,
            updated_at=now,
            expires_at=now + timedelta(days=30),
            used_at=None,
            revoked_at=None,
        )
    )
    session.commit()


def test_second_apply_same_credit_same_session_returns_not_applied(engine):
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    db = Session()
    try:
        _insert_available_credit(db, credit_id="credit-a", user_id="user-1")

        first = apply_credit_for_checkout(
            db=db,
            user_id="user-1",
            base_amount_cents=1000,
            order_currency="BRL",
            order_id="order-1",
            use_credit=True,
            requested_credit_id="credit-a",
        )
        assert first.applied is True
        assert first.discount_cents == 500
        assert first.final_amount_cents == 500

        second = apply_credit_for_checkout(
            db=db,
            user_id="user-1",
            base_amount_cents=1000,
            order_currency="BRL",
            order_id="order-2",
            use_credit=True,
            requested_credit_id="credit-a",
        )
        assert second.applied is False
        assert second.reason == "no_eligible_credit"
        assert second.discount_cents == 0
        assert second.final_amount_cents == 1000

        db.commit()
    finally:
        db.close()

    verify = sessionmaker(bind=engine, future=True)()
    try:
        row = verify.query(Credit).filter(Credit.id == "credit-a").one()
        assert row.status == CreditStatus.USED
    finally:
        verify.close()


@pytest.mark.skipif(
    not os.getenv("ORDER_PICKUP_TEST_DATABASE_URL"),
    reason="Defina ORDER_PICKUP_TEST_DATABASE_URL (Postgres) para validar concorrência com FOR UPDATE.",
)
def test_concurrent_apply_same_credit_only_one_applies_postgres():
    """Duas sessões disputam o mesmo crédito; exatamente um apply deve vencer (Postgres)."""
    url = os.environ["ORDER_PICKUP_TEST_DATABASE_URL"]
    eng = create_engine(url, future=True)
    suffix = uuid.uuid4().hex[:10]
    credit_id = f"credit-conc-{suffix}"
    user_id = f"user-conc-{suffix}"

    Session = sessionmaker(bind=eng, autoflush=False, autocommit=False, future=True)
    try:
        Base.metadata.create_all(bind=eng, tables=[Credit.__table__])
        seed = Session()
        try:
            _insert_available_credit(seed, credit_id=credit_id, user_id=user_id, amount_cents=400)
        finally:
            seed.close()

        barrier = threading.Barrier(2)
        results: list = []
        errors: list = []

        def worker():
            s = Session()
            try:
                barrier.wait()
                r = apply_credit_for_checkout(
                    db=s,
                    user_id=user_id,
                    base_amount_cents=900,
                    order_currency="BRL",
                    order_id=None,
                    use_credit=True,
                    requested_credit_id=credit_id,
                )
                s.commit()
                results.append(r)
            except Exception as exc:  # noqa: BLE001 — test harness
                errors.append(exc)
                s.rollback()
            finally:
                s.close()

        t1 = threading.Thread(target=worker)
        t2 = threading.Thread(target=worker)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        assert not errors, f"worker raised: {errors}"
        applied_count = sum(1 for r in results if r.applied)
        assert applied_count == 1

        verify = Session()
        try:
            row = verify.query(Credit).filter(Credit.id == credit_id).one()
            assert row.status == CreditStatus.USED
        finally:
            verify.close()
    finally:
        cleanup = Session()
        try:
            cleanup.query(Credit).filter(Credit.id == credit_id).delete(synchronize_session=False)
            cleanup.commit()
        finally:
            cleanup.close()
        eng.dispose()


def test_restore_credit_after_failed_order_creation_reopens_used(engine):
    Session = sessionmaker(bind=engine, future=True)
    db = Session()
    try:
        _insert_available_credit(db, credit_id="credit-c", user_id="user-3", amount_cents=300)
        applied = apply_credit_for_checkout(
            db=db,
            user_id="user-3",
            base_amount_cents=800,
            order_currency="BRL",
            order_id="order-x",
            use_credit=True,
            requested_credit_id="credit-c",
        )
        assert applied.applied is True
        db.commit()

        meta = {
            "credit_application": {
                "applied": True,
                "credit_id": "credit-c",
                "discount_cents": 300,
            }
        }
        restored = restore_credit_after_failed_order_creation(db=db, order_metadata=meta)
        assert restored is True
        db.commit()

        row = db.query(Credit).filter(Credit.id == "credit-c").one()
        assert row.status == CreditStatus.AVAILABLE
        assert row.used_at is None
    finally:
        db.close()
