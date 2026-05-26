"""Sincroniza catálogo mundial → partner_programs e plan entitlements."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.subscriptions_global_players import GLOBAL_SUBSCRIPTION_PLAYERS, tier_player_map_from_registry


def sync_global_players_to_db(db: Session) -> dict[str, int]:
    now = datetime.now(timezone.utc)
    created_programs = 0
    created_entitlements = 0
    updated_plans = 0

    tier_map = tier_player_map_from_registry()
    is_sqlite = db.bind.dialect.name == "sqlite"
    for plan_code, codes in tier_map.items():
        features = json.dumps({"tier": plan_code.lower(), "players": codes, "player_count": len(codes)})
        if is_sqlite:
            db.execute(
                text("UPDATE subscription_plans SET features_json = :features, updated_at = :now WHERE code = :code"),
                {"code": plan_code, "features": features, "now": now},
            )
        else:
            db.execute(
                text(
                    """
                    UPDATE subscription_plans
                    SET features_json = CAST(:features AS jsonb), updated_at = :now
                    WHERE code = :code
                    """
                ),
                {"code": plan_code, "features": features, "now": now},
            )
        updated_plans += 1

    for p in GLOBAL_SUBSCRIPTION_PLAYERS:
        code = str(p["code"])
        if not db.execute(
            text("SELECT 1 FROM subscription_partner_programs WHERE partner_code = :c LIMIT 1"),
            {"c": code},
        ).scalar():
            db.execute(
                text(
                    """
                    INSERT INTO subscription_partner_programs (
                        id, partner_code, partner_name, partner_type, default_plan_code,
                        revenue_share_pct, countries_json, kyb_status, active, created_at, updated_at
                    ) VALUES (:id, :c, :n, :t, :plan, :rev, :countries, 'APPROVED', TRUE, :now, :now)
                    """
                ),
                {
                    "id": str(uuid.uuid4()),
                    "c": code,
                    "n": p["name"],
                    "t": p["player_type"],
                    "plan": p.get("default_plan"),
                    "rev": float(p.get("revenue_share_pct") or 0),
                    "countries": json.dumps(p.get("regions") or []),
                    "now": now,
                },
            )
            created_programs += 1

        for tier in p.get("tier_eligibility") or []:
            if db.execute(
                text(
                    "SELECT 1 FROM subscription_plan_entitlements WHERE plan_code = :p AND player_code = :pl LIMIT 1"
                ),
                {"p": tier, "pl": code},
            ).scalar():
                continue
            prio = 10 if p.get("priority") else 5
            if tier == "ENTERPRISE":
                prio += 2
            db.execute(
                text(
                    """
                    INSERT INTO subscription_plan_entitlements (
                        id, plan_code, player_code, player_name, player_type,
                        region_codes_json, enabled, priority_level, created_at, updated_at
                    ) VALUES (:id, :pc, :pl, :pn, :pt, :regions, TRUE, :prio, :now, :now)
                    """
                ),
                {
                    "id": str(uuid.uuid4()),
                    "pc": tier,
                    "pl": code,
                    "pn": p["name"],
                    "pt": p["player_type"],
                    "regions": json.dumps(p.get("regions") or []),
                    "prio": prio,
                    "now": now,
                },
            )
            created_entitlements += 1

    db.commit()
    return {
        "partner_programs": created_programs,
        "entitlements": created_entitlements,
        "plans_features_updated": updated_plans,
    }
