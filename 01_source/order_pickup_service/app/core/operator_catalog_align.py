"""
Alinha locker_operators com os códigos do catálogo profissional (catalog_global_players).
"""
from __future__ import annotations

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.data.catalog_global_players import LOCKER_OPERATOR_LEGACY_IDS, locker_operator_id

_OPERATOR_FK_TABLES = ("lockers", "pickups")


def _has_player_code_column(db: Session) -> bool:
    bind = db.get_bind()
    cols = {c["name"] for c in inspect(bind).get_columns("locker_operators")}
    return "player_code" in cols


def _repoint_operator_fks(db: Session, old_id: str, new_id: str) -> None:
    for table in _OPERATOR_FK_TABLES:
        bind = db.get_bind()
        if table not in inspect(bind).get_table_names():
            continue
        cols = {c["name"] for c in inspect(bind).get_columns(table)}
        if "operator_id" not in cols:
            continue
        db.execute(
            text(f"UPDATE {table} SET operator_id = :new WHERE operator_id = :old"),
            {"new": new_id, "old": old_id},
        )


def _rename_operator_id(db: Session, old_id: str, new_id: str, player_code: str) -> bool:
    if old_id == new_id:
        db.execute(
            text("UPDATE locker_operators SET player_code = :code WHERE id = :id"),
            {"code": player_code, "id": old_id},
        )
        return True
    has_old = db.execute(
        text("SELECT 1 FROM locker_operators WHERE id = :id LIMIT 1"),
        {"id": old_id},
    ).scalar()
    has_new = db.execute(
        text("SELECT 1 FROM locker_operators WHERE id = :id LIMIT 1"),
        {"id": new_id},
    ).scalar()
    if has_old and has_new:
        _repoint_operator_fks(db, old_id, new_id)
        db.execute(text("DELETE FROM locker_operators WHERE id = :id"), {"id": old_id})
        db.execute(
            text("UPDATE locker_operators SET player_code = :code WHERE id = :id"),
            {"code": player_code, "id": new_id},
        )
        return True
    if has_old and not has_new:
        _repoint_operator_fks(db, old_id, new_id)
        db.execute(
            text("UPDATE locker_operators SET id = :new, player_code = :code WHERE id = :old"),
            {"new": new_id, "old": old_id, "code": player_code},
        )
        return True
    if has_new:
        db.execute(
            text("UPDATE locker_operators SET player_code = :code WHERE id = :id"),
            {"code": player_code, "id": new_id},
        )
        return True
    return False


def align_locker_operators_with_catalog(db: Session) -> int:
    """
    Migra IDs legados (ex. OP-MELI-001) → OP-MERCADO_LIVRE e preenche player_code.
    Retorna quantidade de player_codes aplicados.
    """
    if not _has_player_code_column(db):
        return 0
    aligned = 0
    for player_code, legacy_id in LOCKER_OPERATOR_LEGACY_IDS.items():
        new_id = locker_operator_id(player_code)
        if _rename_operator_id(db, legacy_id, new_id, player_code):
            aligned += 1
    db.commit()
    return aligned
