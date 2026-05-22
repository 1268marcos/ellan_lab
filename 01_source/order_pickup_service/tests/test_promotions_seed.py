from __future__ import annotations

import os
import tempfile

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.promotions_seed import PROMOTIONS_SEED, seed_promotions, seed_promotions_world


def test_seed_promotions_idempotent_sqlite():
    fd, path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    engine = create_engine(f"sqlite:///{path}", future=True)
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE promotion_campaigns (
                    id VARCHAR(36) PRIMARY KEY,
                    code VARCHAR(32) NOT NULL UNIQUE,
                    name VARCHAR(128) NOT NULL,
                    description TEXT,
                    channel_family VARCHAR(32) NOT NULL DEFAULT 'GENERAL',
                    primary_country VARCHAR(8),
                    priority INTEGER NOT NULL DEFAULT 100,
                    max_stack_promotions INTEGER NOT NULL DEFAULT 1,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    valid_from TEXT NOT NULL,
                    valid_until TEXT,
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE promotions (
                    id VARCHAR(36) PRIMARY KEY,
                    code VARCHAR(32),
                    name VARCHAR(128) NOT NULL,
                    type VARCHAR(30) NOT NULL,
                    discount_pct REAL,
                    discount_cents INTEGER,
                    min_order_cents INTEGER NOT NULL DEFAULT 0,
                    max_discount_cents INTEGER,
                    max_uses INTEGER,
                    uses_count INTEGER NOT NULL DEFAULT 0,
                    per_user_limit INTEGER DEFAULT 1,
                    conditions_json TEXT NOT NULL DEFAULT '{}',
                    is_active INTEGER NOT NULL DEFAULT 1,
                    valid_from TEXT NOT NULL,
                    valid_until TEXT,
                    created_by VARCHAR(36),
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                    campaign_id VARCHAR(36)
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE promotion_scopes (
                    id VARCHAR(36) PRIMARY KEY,
                    promotion_id VARCHAR(36) NOT NULL,
                    scope_type VARCHAR(32) NOT NULL,
                    scope_value VARCHAR(128) NOT NULL,
                    mode VARCHAR(16) NOT NULL DEFAULT 'INCLUDE',
                    notes VARCHAR(255),
                    created_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
                """
            )
        )
    Session = sessionmaker(bind=engine, future=True)
    db = Session()
    first = seed_promotions(db, created_by="seed-test")
    assert first["inserted"] == len(PROMOTIONS_SEED)
    assert first["skipped"] == 0
    second = seed_promotions(db, created_by="seed-test")
    assert second["inserted"] == 0
    assert second["skipped"] == len(PROMOTIONS_SEED)
    count = db.execute(text("SELECT COUNT(*) FROM promotions")).scalar()
    assert int(count or 0) == len(PROMOTIONS_SEED)
    db.close()
    engine.dispose()
    os.remove(path)


def test_seed_promotions_world_sqlite():
    fd, path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    engine = create_engine(f"sqlite:///{path}", future=True)
    with engine.begin() as conn:
        for ddl in (
            """
            CREATE TABLE promotion_campaigns (
                id VARCHAR(36) PRIMARY KEY, code VARCHAR(32) NOT NULL UNIQUE,
                name VARCHAR(128) NOT NULL, description TEXT, channel_family VARCHAR(32) NOT NULL DEFAULT 'GENERAL',
                primary_country VARCHAR(8), priority INTEGER NOT NULL DEFAULT 100,
                max_stack_promotions INTEGER NOT NULL DEFAULT 1, is_active INTEGER NOT NULL DEFAULT 1,
                valid_from TEXT NOT NULL, valid_until TEXT, metadata_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE promotions (
                id VARCHAR(36) PRIMARY KEY, code VARCHAR(32), name VARCHAR(128) NOT NULL,
                type VARCHAR(30) NOT NULL, discount_pct REAL, discount_cents INTEGER,
                min_order_cents INTEGER NOT NULL DEFAULT 0, max_discount_cents INTEGER, max_uses INTEGER,
                uses_count INTEGER NOT NULL DEFAULT 0, per_user_limit INTEGER DEFAULT 1,
                conditions_json TEXT NOT NULL DEFAULT '{}', is_active INTEGER NOT NULL DEFAULT 1,
                valid_from TEXT NOT NULL, valid_until TEXT, campaign_id VARCHAR(36),
                created_by VARCHAR(36), created_at TEXT NOT NULL, updated_at TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE promotion_scopes (
                id VARCHAR(36) PRIMARY KEY, promotion_id VARCHAR(36) NOT NULL,
                scope_type VARCHAR(32) NOT NULL, scope_value VARCHAR(128) NOT NULL,
                mode VARCHAR(16) NOT NULL DEFAULT 'INCLUDE', notes VARCHAR(255),
                created_at TEXT NOT NULL
            )
            """,
        ):
            conn.execute(text(ddl))
    Session = sessionmaker(bind=engine, future=True)
    db = Session()
    world = seed_promotions_world(db)
    assert world["promotions_inserted"] == len(PROMOTIONS_SEED)
    assert world["campaigns_inserted"] == 10
    assert world["scopes_inserted"] > 0
    db.close()
    engine.dispose()
    os.remove(path)
