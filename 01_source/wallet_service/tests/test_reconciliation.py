import uuid

from app.core.database import SessionLocal, init_db
from app.models.transaction import Transaction
from app.models.wallet import Wallet
from app.services import reconciliation_service, wallet_service
from app.workers import reconciliation_worker


def test_reconcile_roll_back_on_divergence():
    init_db()
    db = SessionLocal()
    try:
        w = Wallet(user_id="div", balance=999, version=1)
        db.add(w)
        db.add(
            Transaction(
                user_id="div",
                amount=10,
                tx_type="credit",
                status="completed",
                transaction_id=f"only-{uuid.uuid4()}",
            )
        )
        db.commit()
        rep = reconciliation_service.reconcile_user(db, "div")
        assert rep["divergent"] is True
        assert rep["rolled_back"] is True
        db.refresh(w)
        assert w.balance == 10
    finally:
        db.close()


def test_reconcile_worker_with_session():
    init_db()
    from app.core.database import SessionLocal

    rep = reconciliation_worker.run_nightly(SessionLocal)
    assert isinstance(rep, list)


def test_reconcile_worker_pass_db():
    init_db()
    db = SessionLocal()
    try:
        rep = reconciliation_worker.run_nightly(SessionLocal, db=db)
        assert isinstance(rep, list)
    finally:
        db.close()


def test_reconcile_missing_wallet():
    init_db()
    db = SessionLocal()
    try:
        rep = reconciliation_service.reconcile_user(db, "missing")
        assert rep["divergent"] is False
    finally:
        db.close()


def test_reconcile_aligned():
    init_db()
    db = SessionLocal()
    try:
        wallet_service.credit_wallet(db, None, "ok", 5, "a1", "credit")
        rep = reconciliation_service.reconcile_user(db, "ok")
        assert rep["divergent"] is False
    finally:
        db.close()
