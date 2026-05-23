"""Seed de funcionalidades premium rental (onboarding, SLA breaches, settlements, etc.)."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session


def _now() -> datetime:
    return datetime.now(timezone.utc)


def seed_rental_premium(db: Session) -> dict[str, int]:
    now = _now()
    counts = {
        "onboarding": 0,
        "sla_breaches": 0,
        "settlements": 0,
        "capacity_snapshots": 0,
        "disputes": 0,
        "renewal_offers": 0,
    }

    onboarding_specs = [
        ("INPOST", "LIVE", "PREMIUM", 92.5),
        ("MAGALU", "APPROVED", "STANDARD", 88.0),
        ("MELI", "COMPLIANCE_REVIEW", "ENTERPRISE", 76.5),
        ("CORREIOS", "KYC_SUBMITTED", "STANDARD", None),
        ("SHOPEE", "DRAFT", "STANDARD", None),
    ]
    for code, status, tier, score in onboarding_specs:
        net = db.execute(
            text("SELECT id FROM rental_networks WHERE code = :c LIMIT 1"),
            {"c": code},
        ).mappings().first()
        if not net:
            continue
        nid = str(net["id"])
        if db.execute(
            text("SELECT id FROM rental_network_onboarding WHERE network_id = :n"),
            {"n": nid},
        ).mappings().first():
            continue
        docs = json.dumps([{"type": "KYB", "status": "verified" if status == "LIVE" else "pending"}])
        db.execute(
            text(
                """
                INSERT INTO rental_network_onboarding (
                    id, network_id, status, kyb_tier, compliance_score, documents_json,
                    reviewer, submitted_at, approved_at, live_at, created_at, updated_at
                ) VALUES (
                    :id, :nid, :st, :tier, :score, :docs, :rev,
                    :sub, :app, :live, :now, :now
                )
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "nid": nid,
                "st": status,
                "tier": tier,
                "score": score,
                "docs": docs,
                "rev": "ops@ellan.lab" if status in ("APPROVED", "LIVE") else None,
                "sub": now - timedelta(days=14) if status != "DRAFT" else None,
                "app": now - timedelta(days=7) if status in ("APPROVED", "LIVE") else None,
                "live": now - timedelta(days=3) if status == "LIVE" else None,
                "now": now,
            },
        )
        counts["onboarding"] += 1

    networks = db.execute(
        text("SELECT id, code FROM rental_networks WHERE active = TRUE ORDER BY code LIMIT 5")
    ).mappings().all()
    for n in networks[:3]:
        nid = str(n["id"])
        for days_ago in range(7):
            snap = now.date() - timedelta(days=days_ago)
            if db.execute(
                text(
                    "SELECT id FROM rental_capacity_snapshots WHERE network_id = :n AND snapshot_date = :d"
                ),
                {"n": nid, "d": snap},
            ).mappings().first():
                continue
            total = 120 + days_ago * 2
            occupied = min(total - 10, 70 + days_ago * 3)
            util = round(occupied / total * 100, 2)
            db.execute(
                text(
                    """
                    INSERT INTO rental_capacity_snapshots (
                        id, network_id, snapshot_date, total_slots, occupied_slots,
                        reserved_slots, utilization_pct, peak_hour_local, created_at
                    ) VALUES (
                        :id, :nid, :d, :tot, :occ, 5, :util, 18, :now
                    )
                    """
                ),
                {
                    "id": str(uuid.uuid4()),
                    "nid": nid,
                    "d": snap,
                    "tot": total,
                    "occ": occupied,
                    "util": util,
                    "now": now,
                },
            )
            counts["capacity_snapshots"] += 1

    for s in db.execute(
        text("SELECT id, network_id, metric_code, target_value FROM rental_sla_policies LIMIT 3")
    ).mappings().all():
        if db.execute(
            text("SELECT id FROM rental_sla_breach_incidents WHERE sla_policy_id = :s LIMIT 1"),
            {"s": str(s["id"])},
        ).mappings().first():
            continue
        measured = float(s["target_value"]) * 0.92
        db.execute(
            text(
                """
                INSERT INTO rental_sla_breach_incidents (
                    id, network_id, sla_policy_id, metric_code, target_value, measured_value,
                    severity, status, penalty_cents, currency, detected_at, created_at
                ) VALUES (
                    :id, :nid, :sid, :mc, :tv, :mv, 'MEDIUM', 'OPEN', 2500, 'BRL', :now, :now
                )
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "nid": str(s["network_id"]),
                "sid": str(s["id"]),
                "mc": str(s["metric_code"]),
                "tv": float(s["target_value"]),
                "mv": measured,
                "now": now,
            },
        )
        counts["sla_breaches"] += 1

    op = db.execute(
        text("SELECT id FROM rental_operators WHERE status = 'ACTIVE' LIMIT 1")
    ).mappings().first()
    if op and not db.execute(text("SELECT id FROM rental_settlement_batches LIMIT 1")).mappings().first():
        gross = 450000
        comm = 15750
        db.execute(
            text(
                """
                INSERT INTO rental_settlement_batches (
                    id, operator_id, batch_code, period_start, period_end,
                    gross_cents, commission_cents, adjustments_cents, net_cents,
                    currency, status, approved_by, created_at, updated_at
                ) VALUES (
                    :id, :oid, :code, :start, :end, :gross, :comm, 0, :net,
                    'BRL', 'APPROVED', 'finance@ellan.lab', :now, :now
                )
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "oid": str(op["id"]),
                "code": f"STL-{now.strftime('%Y%m')}-001",
                "start": now - timedelta(days=30),
                "end": now,
                "gross": gross,
                "comm": comm,
                "net": gross - comm,
                "now": now,
            },
        )
        counts["settlements"] += 1

    contract = db.execute(
        text("SELECT id, amount_cents FROM rental_contracts WHERE status = 'ACTIVE' LIMIT 1")
    ).mappings().first()
    if contract:
        cid = str(contract["id"])
        if not db.execute(
            text("SELECT id FROM rental_contract_disputes WHERE contract_id = :c LIMIT 1"),
            {"c": cid},
        ).mappings().first():
            db.execute(
                text(
                    """
                    INSERT INTO rental_contract_disputes (
                        id, contract_id, dispute_type, amount_cents, currency, status,
                        reason, opened_at, created_at
                    ) VALUES (
                        :id, :cid, 'BILLING', 4900, 'BRL', 'UNDER_REVIEW',
                        'Divergência de ciclo de cobrança', :now, :now
                    )
                    """
                ),
                {"id": str(uuid.uuid4()), "cid": cid, "now": now},
            )
            counts["disputes"] += 1
        if not db.execute(
            text("SELECT id FROM rental_renewal_offers WHERE contract_id = :c LIMIT 1"),
            {"c": cid},
        ).mappings().first():
            db.execute(
                text(
                    """
                    INSERT INTO rental_renewal_offers (
                        id, contract_id, offer_amount_cents, currency, billing_cycle,
                        valid_until, status, auto_renew, sent_at, created_at
                    ) VALUES (
                        :id, :cid, :amt, 'BRL', 'MONTHLY', :valid, 'PENDING', TRUE, :now, :now
                    )
                    """
                ),
                {
                    "id": str(uuid.uuid4()),
                    "cid": cid,
                    "amt": int(contract["amount_cents"]),
                    "valid": now + timedelta(days=14),
                    "now": now,
                },
            )
            counts["renewal_offers"] += 1

    return counts
