"""Sincroniza relações entre redes rental e ligação a global_players."""
from __future__ import annotations

import json
import uuid
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.rental_locker_ecosystem import ECOSYSTEM_NETWORK_RELATIONS


def _network_id_by_code(db: Session, code: str) -> str | None:
    row = db.execute(
        text("SELECT id FROM rental_networks WHERE code = :c LIMIT 1"),
        {"c": code.strip().upper()},
    ).mappings().first()
    return str(row["id"]) if row else None


def seed_rental_network_relations(db: Session) -> int:
    """Insere parcerias idempotentes (from/to por code)."""
    created = 0
    for from_code, to_code, relation_type, integration_mode in ECOSYSTEM_NETWORK_RELATIONS:
        from_id = _network_id_by_code(db, from_code)
        to_id = _network_id_by_code(db, to_code)
        if not from_id or not to_id:
            continue
        exists = db.execute(
            text(
                """
                SELECT id FROM rental_network_relations
                WHERE from_network_id = :f AND to_network_id = :t AND relation_type = :rt
                """
            ),
            {"f": from_id, "t": to_id, "rt": relation_type},
        ).mappings().first()
        if exists:
            continue
        db.execute(
            text(
                """
                INSERT INTO rental_network_relations (
                    id, from_network_id, to_network_id, relation_type,
                    integration_mode, metadata_json, active, created_at
                ) VALUES (
                    :id, :f, :t, :rt, :im, :meta, TRUE, CURRENT_TIMESTAMP
                )
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "f": from_id,
                "t": to_id,
                "rt": relation_type,
                "im": integration_mode,
                "meta": json.dumps({"from_code": from_code, "to_code": to_code}),
            },
        )
        created += 1
    return created


def count_global_player_links(db: Session) -> dict[str, Any]:
    """Quantifica redes com código global e players existentes no registry."""
    rows = db.execute(
        text(
            """
            SELECT rn.code, rn.global_player_code
            FROM rental_networks rn
            WHERE rn.global_player_code IS NOT NULL AND rn.global_player_code != ''
            """
        )
    ).mappings().all()
    linked = 0
    missing: list[str] = []
    for r in rows:
        gp = str(r["global_player_code"])
        found = db.execute(
            text("SELECT 1 FROM global_players WHERE code = :c LIMIT 1"),
            {"c": gp},
        ).scalar()
        if found:
            linked += 1
        else:
            missing.append(gp)
    return {
        "networks_with_global_code": len(rows),
        "linked_to_registry": linked,
        "missing_in_registry": sorted(set(missing)),
    }
