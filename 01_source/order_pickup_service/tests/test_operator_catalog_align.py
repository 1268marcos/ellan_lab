from __future__ import annotations

import os
import tempfile

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.operator_catalog_align import align_locker_operators_with_catalog
from app.data.catalog_global_players import locker_operator_id


def test_align_migrates_legacy_operator_id():
    fd, path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    engine = create_engine(f"sqlite:///{path}", future=True)
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE locker_operators (
                    id VARCHAR(64) PRIMARY KEY,
                    name VARCHAR(128) NOT NULL,
                    player_code VARCHAR(40),
                    operator_type VARCHAR(32) NOT NULL DEFAULT 'LOGISTICS',
                    country VARCHAR(2) NOT NULL DEFAULT 'BR',
                    active INTEGER NOT NULL DEFAULT 1,
                    currency VARCHAR(8) NOT NULL DEFAULT 'BRL',
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT DEFAULT (datetime('now'))
                )
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO locker_operators (id, name, player_code, operator_type, country)
                VALUES ('OP-MELI-001', 'Mercado Livre', NULL, 'ECOMMERCE', 'BR')
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE lockers (
                    id VARCHAR(36) PRIMARY KEY,
                    operator_id VARCHAR(64)
                )
                """
            )
        )
        conn.execute(
            text("INSERT INTO lockers (id, operator_id) VALUES ('lk-1', 'OP-MELI-001')")
        )
    Session = sessionmaker(bind=engine, future=True)
    db = Session()
    n = align_locker_operators_with_catalog(db)
    assert n >= 1
    new_id = locker_operator_id("MERCADO_LIVRE")
    row = db.execute(
        text("SELECT id, player_code FROM locker_operators WHERE id = :id"),
        {"id": new_id},
    ).mappings().first()
    assert row is not None
    assert row["player_code"] == "MERCADO_LIVRE"
    lk = db.execute(
        text("SELECT operator_id FROM lockers WHERE id = 'lk-1'"),
    ).scalar()
    assert lk == new_id
    db.close()
    engine.dispose()
    os.remove(path)
