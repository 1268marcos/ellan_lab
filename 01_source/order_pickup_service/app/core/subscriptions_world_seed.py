"""Seed de funcionalidades mundiais: preços regionais, add-ons, pausas, SLA, settlements, retenção, consent."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

REGIONS = (
    ("BR", "BRL"),
    ("PT", "EUR"),
    ("EU", "EUR"),
    ("UK", "GBP"),
    ("US", "USD"),
)

PLAN_BASE_FEES = {
    "BASIC": 990,
    "PREMIUM": 2490,
    "PRO": 4990,
    "ENTERPRISE": 9990,
}

REGION_MULTIPLIER = {
    "BR": 1.0,
    "PT": 0.22,
    "EU": 0.20,
    "UK": 0.18,
    "US": 0.19,
}


def seed_subscriptions_world(db: Session) -> dict[str, int]:
    now = datetime.now(timezone.utc)
    stats = {
        "regional_prices": 0,
        "plan_addons": 0,
        "active_addons": 0,
        "pause_periods": 0,
        "sla_targets": 0,
        "settlements": 0,
        "retention_offers": 0,
        "consent_records": 0,
    }

    for plan_code, base in PLAN_BASE_FEES.items():
        for region, currency in REGIONS:
            mult = REGION_MULTIPLIER[region]
            monthly = int(base * mult) if region != "BR" else base
            yearly = monthly * 10
            exists = db.execute(
                text(
                    "SELECT 1 FROM subscription_regional_prices WHERE plan_code = :p AND region_code = :r LIMIT 1"
                ),
                {"p": plan_code, "r": region},
            ).scalar()
            if exists:
                continue
            db.execute(
                text(
                    """
                    INSERT INTO subscription_regional_prices (
                        id, plan_code, region_code, currency, monthly_fee_cents, yearly_fee_cents,
                        tax_inclusive, active, created_at, updated_at
                    ) VALUES (:id, :plan, :reg, :cur, :m, :y, TRUE, TRUE, :now, :now)
                    """
                ),
                {
                    "id": str(uuid.uuid4()),
                    "plan": plan_code,
                    "reg": region,
                    "cur": currency,
                    "m": monthly,
                    "y": yearly,
                    "now": now,
                },
            )
            stats["regional_prices"] += 1

    addons = [
        ("EXTRA_LOCKER_NETWORK", "Rede locker extra", "NETWORK", 490, "BASIC", ["BR", "PT", "EU"]),
        ("FAMILY_SEAT", "Assento familiar (+3)", "SEATS", 990, "PREMIUM", ["BR", "PT", "EU", "US"]),
        ("PRIORITY_INSURANCE", "Seguro envio prioritário", "INSURANCE", 390, "PRO", ["BR", "EU", "UK"]),
        ("FOOD_PASS", "Passe food delivery", "FOOD", 590, "PREMIUM", ["BR"]),
        ("CARBON_OFFSET", "Compensação carbono", "ESG", 190, "BASIC", ["BR", "EU", "US", "UK"]),
    ]
    for code, name, atype, fee, min_plan, regions in addons:
        if db.execute(
            text("SELECT 1 FROM subscription_plan_addons WHERE code = :c LIMIT 1"), {"c": code}
        ).scalar():
            continue
        db.execute(
            text(
                """
                INSERT INTO subscription_plan_addons (
                    id, code, name, addon_type, monthly_fee_cents, min_plan_code,
                    regions_json, active, metadata_json, created_at, updated_at
                ) VALUES (:id, :code, :name, :atype, :fee, :min_plan, :regions, TRUE, '{}', :now, :now)
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "code": code,
                "name": name,
                "atype": atype,
                "fee": fee,
                "min_plan": min_plan,
                "regions": json.dumps(regions),
                "now": now,
            },
        )
        stats["plan_addons"] += 1

    subs = db.execute(
        text("SELECT id, plan_type, user_id FROM customer_subscriptions LIMIT 5")
    ).mappings().all()
    for sub in subs:
        sid = str(sub["id"])
        if db.execute(
            text("SELECT 1 FROM subscription_active_addons WHERE subscription_id = :s LIMIT 1"),
            {"s": sid},
        ).scalar():
            continue
        addon_code = "FAMILY_SEAT" if str(sub["plan_type"]) in ("PREMIUM", "PRO", "ENTERPRISE") else "CARBON_OFFSET"
        fee = 990 if addon_code == "FAMILY_SEAT" else 190
        db.execute(
            text(
                """
                INSERT INTO subscription_active_addons (
                    id, subscription_id, addon_code, status, monthly_fee_cents, started_at, created_at
                ) VALUES (:id, :sid, :code, 'ACTIVE', :fee, :now, :now)
                """
            ),
            {"id": str(uuid.uuid4()), "sid": sid, "code": addon_code, "fee": fee, "now": now},
        )
        stats["active_addons"] += 1

        if not db.execute(
            text("SELECT 1 FROM subscription_pause_periods WHERE subscription_id = :s LIMIT 1"),
            {"s": sid},
        ).scalar():
            db.execute(
                text(
                    """
                    INSERT INTO subscription_pause_periods (
                        id, subscription_id, pause_start, pause_end, reason, status, created_at
                    ) VALUES (:id, :sid, :start, :end, 'TRAVEL', 'SCHEDULED', :now)
                    """
                ),
                {
                    "id": str(uuid.uuid4()),
                    "sid": sid,
                    "start": now + timedelta(days=30),
                    "end": now + timedelta(days=44),
                    "now": now,
                },
            )
            stats["pause_periods"] += 1

        if not db.execute(
            text(
                "SELECT 1 FROM subscription_retention_offers WHERE subscription_id = :s AND status = 'OFFERED' LIMIT 1"
            ),
            {"s": sid},
        ).scalar():
            db.execute(
                text(
                    """
                    INSERT INTO subscription_retention_offers (
                        id, subscription_id, offer_code, discount_pct, bonus_months,
                        valid_until, status, created_at
                    ) VALUES (:id, :sid, 'STAY20', 20, 1, :valid, 'OFFERED', :now)
                    """
                ),
                {
                    "id": str(uuid.uuid4()),
                    "sid": sid,
                    "valid": now + timedelta(days=14),
                    "now": now,
                },
            )
            stats["retention_offers"] += 1

    sla_defs = [
        ("BASIC", None, "LOCKER_UPTIME", 99.0, "PCT", "Disponibilidade rede locker"),
        ("PREMIUM", "BR", "SUPPORT_RESPONSE_HOURS", 24, "HOURS", "SLA suporte BR"),
        ("PRO", "EU", "LOCKER_UPTIME", 99.5, "PCT", "Uptime EU InPost/DPD"),
        ("ENTERPRISE", None, "DEDICATED_CSM", 1, "BOOL", "Customer success dedicado"),
        ("PRO", "US", "FOOD_HANDOFF_MIN", 45, "MINUTES", "SLA handoff food US"),
    ]
    for plan, region, metric, val, unit, desc in sla_defs:
        if db.execute(
            text(
                "SELECT 1 FROM subscription_sla_targets WHERE plan_code = :p AND metric_code = :m LIMIT 1"
            ),
            {"p": plan, "m": metric},
        ).scalar():
            continue
        db.execute(
            text(
                """
                INSERT INTO subscription_sla_targets (
                    id, plan_code, region_code, metric_code, target_value, unit, description, active, created_at
                ) VALUES (:id, :plan, :reg, :metric, :val, :unit, :desc, TRUE, :now)
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "plan": plan,
                "reg": region,
                "metric": metric,
                "val": val,
                "unit": unit,
                "desc": desc,
                "now": now,
            },
        )
        stats["sla_targets"] += 1

    period_month = now.strftime("%Y-%m")
    for partner, share, gross in (("magalu", 12.5, 125000), ("mercado_livre", 10.0, 98000), ("inpost", 8.0, 45000)):
        if db.execute(
            text(
                "SELECT 1 FROM subscription_partner_settlements WHERE partner_code = :p AND period_month = :m LIMIT 1"
            ),
            {"p": partner, "m": period_month},
        ).scalar():
            continue
        net = int(gross * share / 100)
        db.execute(
            text(
                """
                INSERT INTO subscription_partner_settlements (
                    id, partner_code, period_month, subscription_count, gross_cents, share_pct,
                    net_cents, currency, status, created_at
                ) VALUES (:id, :p, :pm, :cnt, :gross, :share, :net, 'BRL', 'OPEN', :now)
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "p": partner,
                "pm": period_month,
                "cnt": max(1, gross // 5000),
                "gross": gross,
                "share": share,
                "net": net,
                "now": now,
            },
        )
        stats["settlements"] += 1

    for uid in ("demo-user-magalu", "demo-user-inpost", "demo-user-enterprise"):
        if db.execute(
            text("SELECT 1 FROM subscription_consent_records WHERE user_id = :u LIMIT 1"), {"u": uid}
        ).scalar():
            continue
        for ctype, ver in (("TERMS_OF_SERVICE", "2026.1"), ("PRIVACY_POLICY", "2026.1"), ("MARKETING_OPT_IN", "2026.1")):
            db.execute(
                text(
                    """
                    INSERT INTO subscription_consent_records (
                        id, user_id, consent_type, policy_version, locale, accepted_at, metadata_json
                    ) VALUES (:id, :u, :ct, :ver, 'pt-BR', :now, '{}')
                    """
                ),
                {"id": str(uuid.uuid4()), "u": uid, "ct": ctype, "ver": ver, "now": now},
            )
            stats["consent_records"] += 1

    db.commit()
    return stats
