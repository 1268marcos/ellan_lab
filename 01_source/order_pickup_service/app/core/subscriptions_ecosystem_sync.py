"""Sincroniza ecossistema completo: players, relações, canais, food handoffs, global_players."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.subscriptions_ecosystem_relations import SUBSCRIPTION_PLAYER_RELATIONS
from app.core.subscriptions_global_players import GLOBAL_SUBSCRIPTION_PLAYERS


def _segment_flags(segment: str) -> tuple[bool, bool, bool, bool]:
    seg = segment.upper()
    return (
        seg in {"PARCEL_LOCKER", "HARDWARE_VENDOR"},
        seg in {"PUDO_RETAIL", "COLLECTION_POINT"},
        seg == "FOOD_DELIVERY",
        seg == "MARKETPLACE",
    )


def sync_ecosystem_players_catalog(db: Session) -> int:
    now = datetime.now(timezone.utc)
    created = 0
    for p in GLOBAL_SUBSCRIPTION_PLAYERS:
        code = str(p["code"])
        if db.execute(
            text("SELECT 1 FROM subscription_ecosystem_players WHERE code = :c LIMIT 1"),
            {"c": code},
        ).scalar():
            continue
        sl, sp, sf, sm = _segment_flags(str(p.get("segment") or ""))
        db.execute(
            text(
                """
                INSERT INTO subscription_ecosystem_players (
                    code, name, player_type, segment, regions_json, default_plan_code,
                    revenue_share_pct, integration_modes_json,
                    supports_lockers, supports_pudo, supports_food, supports_marketplace,
                    priority_flag, active, created_at, updated_at
                ) VALUES (
                    :code, :name, :ptype, :seg, :regions, :plan, :rev, :modes,
                    :sl, :sp, :sf, :sm, :pri, TRUE, :now, :now
                )
                """
            ),
            {
                "code": code,
                "name": p["name"],
                "ptype": p["player_type"],
                "seg": p.get("segment"),
                "regions": json.dumps(p.get("regions") or []),
                "plan": p.get("default_plan"),
                "rev": float(p.get("revenue_share_pct") or 0),
                "modes": json.dumps(p.get("integration_modes") or ["API"]),
                "sl": sl,
                "sp": sp,
                "sf": sf,
                "sm": sm,
                "pri": bool(p.get("priority")),
                "now": now,
            },
        )
        created += 1
    return created


def sync_player_relations(db: Session) -> int:
    now = datetime.now(timezone.utc)
    created = 0
    for rel in SUBSCRIPTION_PLAYER_RELATIONS:
        key = (rel["from"], rel["to"], rel["type"])
        if db.execute(
            text(
                """
                SELECT 1 FROM subscription_player_relations
                WHERE from_player_code = :f AND to_player_code = :t AND relation_type = :rt LIMIT 1
                """
            ),
            {"f": key[0], "t": key[1], "rt": key[2]},
        ).scalar():
            continue
        db.execute(
            text(
                """
                INSERT INTO subscription_player_relations (
                    id, from_player_code, to_player_code, relation_type, integration_mode,
                    min_plan_code, notes, active, created_at, updated_at
                ) VALUES (:id, :f, :t, :rt, :mode, :plan, :notes, TRUE, :now, :now)
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "f": rel["from"],
                "t": rel["to"],
                "rt": rel["type"],
                "mode": rel["mode"],
                "plan": rel.get("min_plan"),
                "notes": rel.get("notes"),
                "now": now,
            },
        )
        created += 1
    return created


def sync_integration_channels(db: Session) -> int:
    now = datetime.now(timezone.utc)
    created = 0
    defaults: list[tuple[str, str, str, list[str]]] = []
    for p in GLOBAL_SUBSCRIPTION_PLAYERS:
        code = str(p["code"])
        modes = p.get("integration_modes") or ["API"]
        for mode in modes:
            kind = "WEBHOOK" if mode == "WEBHOOK" else "API"
            defaults.append((code, kind, mode, ["subscription.created", "subscription.renewed"]))
    for code, kind, auth, events in defaults:
        if db.execute(
            text(
                """
                SELECT 1 FROM subscription_integration_channels
                WHERE player_code = :p AND channel_kind = :k LIMIT 1
                """
            ),
            {"p": code, "k": kind},
        ).scalar():
            continue
        db.execute(
            text(
                """
                INSERT INTO subscription_integration_channels (
                    id, player_code, channel_kind, direction, auth_type,
                    webhook_events_json, config_json, active, created_at, updated_at
                ) VALUES (:id, :p, :k, 'OUTBOUND', :auth, :events, '{}', TRUE, :now, :now)
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "p": code,
                "k": kind,
                "auth": auth,
                "events": json.dumps(events),
                "now": now,
            },
        )
        created += 1
    return created


def sync_food_delivery_handoffs(db: Session) -> int:
    now = datetime.now(timezone.utc)
    created = 0
    for rel in SUBSCRIPTION_PLAYER_RELATIONS:
        if rel["type"] != "FOOD_HANDOFF":
            continue
        if db.execute(
            text(
                """
                SELECT 1 FROM subscription_food_delivery_handoffs
                WHERE food_platform_code = :f AND pickup_player_code = :p LIMIT 1
                """
            ),
            {"f": rel["from"], "p": rel["to"]},
        ).scalar():
            continue
        handoff = "LOCKER" if rel["to"] in {"inpost", "dhl", "dpd", "amazon"} else "PUDO"
        db.execute(
            text(
                """
                INSERT INTO subscription_food_delivery_handoffs (
                    id, food_platform_code, pickup_player_code, handoff_type,
                    sla_minutes, min_plan_code, integration_mode, active, created_at, updated_at
                ) VALUES (:id, :food, :pickup, :ht, 45, :plan, :mode, TRUE, :now, :now)
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "food": rel["from"],
                "pickup": rel["to"],
                "ht": handoff,
                "plan": rel.get("min_plan") or "PREMIUM",
                "mode": rel["mode"],
                "now": now,
            },
        )
        created += 1
    return created


def _global_players_table_exists(db: Session) -> bool:
    try:
        if db.bind.dialect.name == "sqlite":
            row = db.execute(
                text("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'global_players' LIMIT 1")
            ).scalar()
        else:
            row = db.execute(
                text(
                    """
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = 'global_players'
                    LIMIT 1
                    """
                )
            ).scalar()
        return bool(row)
    except Exception:
        return False


def sync_to_global_players(db: Session) -> int:
    """Espelha players de assinatura em global_players quando a tabela existir."""
    if not _global_players_table_exists(db):
        return 0

    now = datetime.now(timezone.utc)
    upserted = 0
    for p in GLOBAL_SUBSCRIPTION_PLAYERS:
        code = str(p["code"]).upper()
        regions = p.get("regions") or ["XX"]
        hq = regions[0][:2] if regions else "XX"
        sl, sp, sf, sm = _segment_flags(str(p.get("segment") or ""))
        exists = db.execute(
            text("SELECT 1 FROM global_players WHERE code = :c LIMIT 1"),
            {"c": code},
        ).scalar()
        modes = json.dumps(p.get("integration_modes") or ["API"])
        meta = json.dumps({"subscription_code": p["code"], "segment": p.get("segment")})
        if exists:
            db.execute(
                text(
                    """
                    UPDATE global_players SET
                        name = :name, player_type = :ptype, supports_lockers = :sl,
                        supports_pudo = :sp, supports_food_delivery = :sf,
                        supports_marketplace = :sm, integration_modes_json = :modes,
                        metadata_json = :meta, updated_at = :now, active = TRUE
                    WHERE code = :c
                    """
                ),
                {
                    "c": code,
                    "name": p["name"],
                    "ptype": p["player_type"],
                    "sl": sl,
                    "sp": sp,
                    "sf": sf,
                    "sm": sm,
                    "modes": modes,
                    "meta": meta,
                    "now": now,
                },
            )
        else:
            is_sqlite = db.bind.dialect.name == "sqlite"
            if is_sqlite:
                db.execute(
                    text(
                        """
                        INSERT INTO global_players (
                            code, name, player_type, hq_country,
                            supports_lockers, supports_pudo, supports_food_delivery, supports_marketplace,
                            integration_modes_json, metadata_json, active, created_at, updated_at
                        ) VALUES (
                            :c, :name, :ptype, :hq, :sl, :sp, :sf, :sm, :modes, :meta, 1, :now, :now
                        )
                        """
                    ),
                    {
                        "c": code,
                        "name": p["name"],
                        "ptype": p["player_type"],
                        "hq": hq,
                        "sl": int(sl),
                        "sp": int(sp),
                        "sf": int(sf),
                        "sm": int(sm),
                        "modes": modes,
                        "meta": meta,
                        "now": now,
                    },
                )
            else:
                db.execute(
                    text(
                        """
                        INSERT INTO global_players (
                            code, name, player_type, hq_country,
                            supports_lockers, supports_pudo, supports_food_delivery, supports_marketplace,
                            integration_modes_json, metadata_json, active, created_at, updated_at
                        ) VALUES (
                            :c, :name, :ptype, :hq, :sl, :sp, :sf, :sm,
                            CAST(:modes AS jsonb), CAST(:meta AS jsonb), TRUE, :now, :now
                        )
                        """
                    ),
                    {
                        "c": code,
                        "name": p["name"],
                        "ptype": p["player_type"],
                        "hq": hq,
                        "sl": sl,
                        "sp": sp,
                        "sf": sf,
                        "sm": sm,
                        "modes": modes,
                        "meta": meta,
                        "now": now,
                    },
                )
        upserted += 1
    return upserted


def sync_full_ecosystem(db: Session) -> dict[str, int]:
    from app.core.subscriptions_global_sync import sync_global_players_to_db

    base = sync_global_players_to_db(db)
    stats = {
        "ecosystem_players": sync_ecosystem_players_catalog(db),
        "player_relations": sync_player_relations(db),
        "integration_channels": sync_integration_channels(db),
        "food_handoffs": sync_food_delivery_handoffs(db),
        "global_players_mirror": sync_to_global_players(db),
    }
    stats.update(base)
    db.commit()
    return stats
