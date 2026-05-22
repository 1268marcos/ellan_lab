from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.services.promotion_engine_service import (
    clone_promotion,
    detect_scope_conflicts,
    match_promotions,
    simulate_promotion,
)


def _sqlite_promo_engine():
    fd, path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    engine = create_engine(f"sqlite:///{path}", future=True)
    now = datetime.now(timezone.utc).isoformat()
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE promotions (
                    id TEXT PRIMARY KEY, code TEXT, name TEXT, type TEXT,
                    discount_pct REAL, discount_cents INTEGER, min_order_cents INTEGER DEFAULT 0,
                    max_discount_cents INTEGER, max_uses INTEGER, uses_count INTEGER DEFAULT 0,
                    per_user_limit INTEGER, conditions_json TEXT DEFAULT '{}',
                    is_active INTEGER DEFAULT 1, valid_from TEXT, valid_until TEXT,
                    campaign_id TEXT, created_by TEXT, created_at TEXT, updated_at TEXT
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE promotion_scopes (
                    id TEXT PRIMARY KEY, promotion_id TEXT, scope_type TEXT,
                    scope_value TEXT, mode TEXT DEFAULT 'INCLUDE', notes TEXT, created_at TEXT
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE promotion_product_exclusions (
                    promotion_id TEXT, product_id TEXT, PRIMARY KEY (promotion_id, product_id)
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE promotion_product_inclusions (
                    promotion_id TEXT, product_id TEXT, PRIMARY KEY (promotion_id, product_id)
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE promotion_audit_events (
                    id TEXT PRIMARY KEY, entity_type TEXT, entity_id TEXT, action TEXT,
                    actor_id TEXT, correlation_id TEXT, payload_json TEXT, created_at TEXT
                )
                """
            )
        )
        vf = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        conn.execute(
            text(
                """
                INSERT INTO promotions (
                    id, code, name, type, discount_pct, discount_cents, min_order_cents,
                    is_active, valid_from, conditions_json, uses_count, created_at, updated_at
                ) VALUES
                ('p1', 'MAGALU10', 'Magalu 10', 'PERCENT_OFF', 10, NULL, 1000, 1, :vf, '{}', 0, :n, :n),
                ('p2', 'INPOST-5', 'InPost 5', 'PERCENT_OFF', 5, NULL, 500, 1, :vf, '{}', 0, :n, :n)
                """
            ),
            {"vf": vf, "n": now},
        )
        conn.execute(
            text(
                "INSERT INTO promotion_scopes VALUES ('s1','p1','PLAYER','MAGALU','INCLUDE',NULL,:n)"
            ),
            {"n": now},
        )
        conn.execute(
            text(
                "INSERT INTO promotion_scopes VALUES ('s2','p2','PLAYER','MAGALU','INCLUDE',NULL,:n)"
            ),
            {"n": now},
        )
    return engine, path


def test_simulate_valid():
    engine, path = _sqlite_promo_engine()
    Session = sessionmaker(bind=engine, future=True)
    db = Session()
    out = simulate_promotion(
        db,
        promotion_code="MAGALU10",
        order_id="ORD-1",
        total_amount_cents=10000,
        player_code="MAGALU",
        country_code="BR",
    )
    assert out["valid"] is True
    assert out["discount_cents"] == 1000
    db.close()
    engine.dispose()
    os.remove(path)


def test_match_and_conflicts():
    engine, path = _sqlite_promo_engine()
    Session = sessionmaker(bind=engine, future=True)
    db = Session()
    matches = match_promotions(db, total_amount_cents=10000, player_code="MAGALU", country_code="BR")
    eligible = [m for m in matches if m["eligible"]]
    assert len(eligible) >= 1
    conflicts = detect_scope_conflicts(db)
    assert any(c["scope_value"] == "MAGALU" for c in conflicts)
    db.close()
    engine.dispose()
    os.remove(path)


def test_clone_promotion():
    engine, path = _sqlite_promo_engine()
    Session = sessionmaker(bind=engine, future=True)
    db = Session()
    result = clone_promotion(db, source_promotion_id="p1", new_code="MAGALU10-COPY", actor_id="ops")
    assert result["promotion_code"] == "MAGALU10-COPY"
    row = db.execute(text("SELECT 1 FROM promotions WHERE code = 'MAGALU10-COPY'")).scalar()
    assert row
    audit = db.execute(text("SELECT COUNT(*) FROM promotion_audit_events")).scalar()
    assert int(audit or 0) >= 1
    db.close()
    engine.dispose()
    os.remove(path)
