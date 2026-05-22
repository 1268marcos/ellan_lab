"""Persiste PLAYERS_REGISTRY em global_players e relações."""
from __future__ import annotations

import json
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.data.catalog_global_players import (
    CATEGORY_PLAYER_ELIGIBILITY_SEED,
    locker_operator_id,
)
from app.core.global_players_partner_link import sync_global_players_ecosystem
from app.data.catalog_players_registry import PLAYERS_REGISTRY


def seed_global_players_registry(db: Session, *, sync_ecosystem: bool = True) -> dict[str, int]:
    counts = {"players": 0, "regions": 0, "capabilities": 0, "eligibility": 0, "integrations": 0}

    for p in PLAYERS_REGISTRY:
        code = str(p["code"])
        op_id = locker_operator_id(code) if (
            p.get("supports_lockers") or p.get("supports_marketplace") or p.get("supports_food")
        ) else None
        exists = db.execute(
            text("SELECT 1 FROM global_players WHERE code = :c LIMIT 1"),
            {"c": code},
        ).scalar()
        if not exists:
            db.execute(
                text(
                    """
                    INSERT INTO global_players (
                        code, name, player_type, hq_country,
                        supports_lockers, supports_pudo, supports_food_delivery, supports_marketplace,
                        operator_id, integration_modes_json, metadata_json, active,
                        created_at, updated_at
                    ) VALUES (
                        :code, :name, :ptype, :hq,
                        :lockers, :pudo, :food, :mkt,
                        :op_id, :modes, :meta, TRUE,
                        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                    )
                    """
                ),
                {
                    "code": code,
                    "name": p["name"],
                    "ptype": p["type"],
                    "hq": p["country"],
                    "lockers": bool(p.get("supports_lockers")),
                    "pudo": bool(p.get("supports_pudo")),
                    "food": bool(p.get("supports_food")),
                    "mkt": bool(p.get("supports_marketplace")),
                    "op_id": op_id,
                    "modes": json.dumps(p.get("integration_modes") or []),
                    "meta": json.dumps({"regions": p.get("regions") or []}),
                },
            )
            counts["players"] += 1
        else:
            db.execute(
                text(
                    """
                    UPDATE global_players SET
                        name = :name, player_type = :ptype, hq_country = :hq,
                        supports_lockers = :lockers, supports_pudo = :pudo,
                        supports_food_delivery = :food, supports_marketplace = :mkt,
                        operator_id = COALESCE(:op_id, operator_id),
                        integration_modes_json = :modes,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE code = :code
                    """
                ),
                {
                    "code": code,
                    "name": p["name"],
                    "ptype": p["type"],
                    "hq": p["country"],
                    "lockers": bool(p.get("supports_lockers")),
                    "pudo": bool(p.get("supports_pudo")),
                    "food": bool(p.get("supports_food")),
                    "mkt": bool(p.get("supports_marketplace")),
                    "op_id": op_id,
                    "modes": json.dumps(p.get("integration_modes") or []),
                },
            )

        for country in p.get("regions") or [p["country"]]:
            cc = str(country)[:3].upper()
            if db.execute(
                text(
                    "SELECT 1 FROM global_player_regions WHERE player_code = :p AND country_code = :c"
                ),
                {"p": code, "c": cc},
            ).scalar():
                continue
            db.execute(
                text(
                    """
                    INSERT INTO global_player_regions (id, player_code, country_code, region_code, created_at)
                    VALUES (:id, :p, :c, :r, CURRENT_TIMESTAMP)
                    """
                ),
                {"id": str(uuid4()), "p": code, "c": cc, "r": cc if len(cc) == 2 else None},
            )
            counts["regions"] += 1

        seen_caps: set[str] = set()
        for cap in p.get("capabilities") or []:
            if cap in seen_caps:
                continue
            seen_caps.add(cap)
            if db.execute(
                text(
                    "SELECT 1 FROM global_player_capabilities WHERE player_code = :p AND capability = :cap"
                ),
                {"p": code, "cap": cap},
            ).scalar():
                continue
            db.execute(
                text(
                    """
                    INSERT INTO global_player_capabilities (id, player_code, capability)
                    VALUES (:id, :p, :cap)
                    """
                ),
                {"id": str(uuid4()), "p": code, "cap": cap},
            )
            counts["capabilities"] += 1

        for target_type, flag, key in (
            ("TAXONOMY_SCHEME", p.get("taxonomy_scheme"), code),
            ("CHANNEL_CODE", p.get("channel_listing"), code),
            ("LOCKER_OPERATOR", op_id, op_id),
        ):
            if not flag or not key:
                continue
            if db.execute(
                text(
                    "SELECT 1 FROM global_player_integration_targets "
                    "WHERE player_code = :p AND target_type = :t AND target_key = :k"
                ),
                {"p": code, "t": target_type, "k": key},
            ).scalar():
                continue
            db.execute(
                text(
                    """
                    INSERT INTO global_player_integration_targets (
                        id, player_code, target_type, target_key, metadata_json, created_at
                    ) VALUES (:id, :p, :t, :k, '{}', CURRENT_TIMESTAMP)
                    """
                ),
                {"id": str(uuid4()), "p": code, "t": target_type, "k": key},
            )
            counts["integrations"] += 1

    for cat_id, player_code, eligibility in CATEGORY_PLAYER_ELIGIBILITY_SEED:
        if not db.execute(
            text("SELECT 1 FROM product_categories WHERE id = :id"),
            {"id": cat_id},
        ).scalar():
            continue
        if not db.execute(
            text("SELECT 1 FROM global_players WHERE code = :c"),
            {"c": player_code},
        ).scalar():
            continue
        if db.execute(
            text(
                "SELECT 1 FROM category_player_eligibility WHERE category_id = :cat AND player_code = :p"
            ),
            {"cat": cat_id, "p": player_code},
        ).scalar():
            continue
        db.execute(
            text(
                """
                INSERT INTO category_player_eligibility (
                    id, category_id, player_code, eligibility, created_at
                ) VALUES (:id, :cat, :p, :elig, CURRENT_TIMESTAMP)
                """
            ),
            {"id": str(uuid4()), "cat": cat_id, "p": player_code, "elig": eligibility},
        )
        counts["eligibility"] += 1

    db.commit()
    if sync_ecosystem:
        eco = sync_global_players_ecosystem(db)
        counts["operators_created"] = int(eco.get("operators_created") or 0)
        counts["ecommerce_partners_created"] = int(eco.get("ecommerce_created") or 0)
        counts["logistics_partners_created"] = int(eco.get("logistics_created") or 0)
        counts["ecommerce_links"] = int(eco.get("ecommerce_links") or 0)
        counts["logistics_links"] = int(eco.get("logistics_links") or 0)
    return counts
