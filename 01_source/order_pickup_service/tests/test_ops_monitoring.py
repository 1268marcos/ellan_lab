from __future__ import annotations

import os
import tempfile
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.db import Base
from app.models.credit import Credit, CreditStatus
from app.models.reconciliation_pending import ReconciliationPending
from app.services.ops_monitoring_service import (
    fetch_credits_health,
    fetch_ops_monitoring_summary,
    fetch_reconciliation_lag,
    fetch_runtime_deadlocks,
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@pytest.fixture()
def monitoring_db():
    fd, path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    eng = create_engine(
        f"sqlite:///{path}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    Base.metadata.create_all(
        bind=eng,
        tables=[Credit.__table__, ReconciliationPending.__table__],
    )
    Session = sessionmaker(bind=eng, future=True)
    db = Session()
    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS allocations (
                id TEXT PRIMARY KEY,
                order_id TEXT NOT NULL,
                locker_id TEXT,
                slot INTEGER NOT NULL,
                state TEXT NOT NULL,
                locked_until DATETIME,
                ttl_seconds INTEGER,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL
            )
            """
        )
    )
    db.commit()
    try:
        yield db
    finally:
        db.close()
        eng.dispose()
        try:
            os.unlink(path)
        except OSError:
            pass


def test_fetch_credits_health_counts_and_top_users(monitoring_db):
    now = _utc_now()
    monitoring_db.add(
        Credit(
            id="c1",
            user_id="u1",
            order_id="o1",
            amount_cents=100,
            status=CreditStatus.AVAILABLE,
            created_at=now,
            updated_at=now,
            expires_at=now + timedelta(days=2),
            used_at=None,
            revoked_at=None,
        )
    )
    monitoring_db.add(
        Credit(
            id="c2",
            user_id="u1",
            order_id="o2",
            amount_cents=200,
            status=CreditStatus.USED,
            created_at=now,
            updated_at=now,
            expires_at=now + timedelta(days=30),
            used_at=now,
            revoked_at=None,
        )
    )
    monitoring_db.commit()

    out = fetch_credits_health(monitoring_db, expiring_within_days=7, top_users_limit=5)
    assert out["total_credits"] == 2
    assert out["used_today"] == 1
    assert out["top_users_expiring"][0]["user_id"] == "u1"
    assert out["top_users_expiring"][0]["credits_count"] == 1


def test_fetch_reconciliation_lag_distribution(monitoring_db):
    now = _utc_now()
    monitoring_db.add(
        ReconciliationPending(
            id="rcp1",
            dedupe_key="k1",
            order_id="ord1",
            reason="slot_release_failed",
            status="PENDING",
            payload_json={},
            attempt_count=0,
            max_attempts=5,
            next_retry_at=None,
            processing_started_at=None,
            last_error=None,
            completed_at=None,
            created_at=now - timedelta(hours=2),
            updated_at=now,
        )
    )
    monitoring_db.commit()

    out = fetch_reconciliation_lag(monitoring_db)
    assert out["open_pending_count"] == 1
    assert out["status_distribution"]["PENDING"] == 1
    assert out["max_pending_age_sec"] >= 3600


def test_fetch_runtime_deadlocks_stuck_allocation(monitoring_db):
    old = datetime.now(timezone.utc) - timedelta(hours=3)
    monitoring_db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS allocations (
                id TEXT PRIMARY KEY,
                order_id TEXT NOT NULL,
                locker_id TEXT,
                slot INTEGER NOT NULL,
                state TEXT NOT NULL,
                locked_until DATETIME,
                ttl_seconds INTEGER,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL
            )
            """
        )
    )
    monitoring_db.execute(
        text(
            """
            INSERT INTO allocations
            (id, order_id, locker_id, slot, state, locked_until, created_at, updated_at)
            VALUES
            (:id, :order_id, :locker_id, :slot, :state, NULL, :created_at, :updated_at)
            """
        ),
        {
            "id": "alloc-stuck",
            "order_id": "ord-stuck",
            "locker_id": "LK-1",
            "slot": 3,
            "state": "RESERVED_PAID_PENDING_PICKUP",
            "created_at": old,
            "updated_at": old,
        },
    )
    monitoring_db.commit()

    out = fetch_runtime_deadlocks(monitoring_db, lock_age_sec=3600, limit=10)
    assert out["stuck_count"] == 1
    assert out["items"][0]["allocation_id"] == "alloc-stuck"
    assert out["alert"] is True


def test_fetch_ops_monitoring_summary(monitoring_db):
    summary = fetch_ops_monitoring_summary(monitoring_db)
    assert "credits_health" in summary
    assert "reconciliation_lag" in summary
    assert "runtime_deadlocks" in summary
    assert "alerts" in summary
