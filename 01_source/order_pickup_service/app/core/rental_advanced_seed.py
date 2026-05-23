"""Seed rental avançado: passes, cauções, bloqueios, pricing, dunning, transferências."""
from __future__ import annotations

import hashlib
import uuid
from datetime import timedelta

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.routers.rental_ops_common import utc_now as _utc_now


def seed_rental_advanced(db: Session) -> dict[str, int]:
    now = _utc_now()
    counts = {
        "access_passes": 0,
        "deposits": 0,
        "slot_blocks": 0,
        "pricing_rules": 0,
        "dunning": 0,
        "transfers": 0,
    }

    contract = db.execute(
        text("SELECT id, locker_id, slot_label, amount_cents FROM rental_contracts WHERE status = 'ACTIVE' LIMIT 1")
    ).mappings().first()
    if not contract:
        return counts

    cid = str(contract["id"])
    lid = str(contract["locker_id"])
    slot = str(contract["slot_label"])

    if not db.execute(
        text("SELECT id FROM rental_access_passes WHERE contract_id = :c LIMIT 1"),
        {"c": cid},
    ).mappings().first():
        raw = "482910"
        db.execute(
            text(
                """
                INSERT INTO rental_access_passes (
                    id, contract_id, pass_type, pass_code_hash, pass_hint,
                    valid_from, valid_until, max_uses, use_count, status, created_at
                ) VALUES (
                    :id, :cid, 'PIN', :hash, '48****', :now, :until, 20, 2, 'ACTIVE', :now
                )
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "cid": cid,
                "hash": hashlib.sha256(raw.encode()).hexdigest(),
                "now": now,
                "until": now + timedelta(hours=72),
            },
        )
        counts["access_passes"] += 1

    if not db.execute(
        text("SELECT id FROM rental_deposit_holds WHERE contract_id = :c LIMIT 1"),
        {"c": cid},
    ).mappings().first():
        db.execute(
            text(
                """
                INSERT INTO rental_deposit_holds (
                    id, contract_id, amount_cents, currency, status, hold_reason,
                    payment_ref, held_at, created_at
                ) VALUES (
                    :id, :cid, :amt, 'BRL', 'HELD', 'SECURITY', 'PIX-DEMO', :now, :now
                )
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "cid": cid,
                "amt": max(5000, int(contract["amount_cents"]) // 3),
                "now": now,
            },
        )
        counts["deposits"] += 1

    if not db.execute(text("SELECT id FROM rental_slot_blocks LIMIT 1")).mappings().first():
        db.execute(
            text(
                """
                INSERT INTO rental_slot_blocks (
                    id, locker_id, slot_label, block_type, reason, starts_at, ends_at, created_at
                ) VALUES (
                    :id, :lid, '99Z', 'MAINTENANCE', 'Firmware SwipBox', :start, :end, :now
                )
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "lid": lid,
                "start": now + timedelta(days=2),
                "end": now + timedelta(days=3),
                "now": now,
            },
        )
        counts["slot_blocks"] += 1

    rules = [
        ("INPOST_M_MONTH", "InPost M mensal", "net-inpost", "M", "MONTHLY", 14900, 1.0),
        ("PEAK_SURGE", "Surge fim de ano", None, None, None, 10000, 1.25),
        ("FOOD_HANDOFF_W", "Food delivery semanal", "net-ifood", "S", "WEEKLY", 3900, 1.1),
    ]
    for code, name, nid, size, cycle, base, surge in rules:
        if db.execute(text("SELECT id FROM rental_pricing_rules WHERE code = :c"), {"c": code}).mappings().first():
            continue
        db.execute(
            text(
                """
                INSERT INTO rental_pricing_rules (
                    id, code, name, network_id, slot_size, billing_cycle,
                    base_amount_cents, surge_multiplier, priority, active, created_at
                ) VALUES (
                    :id, :code, :name, :nid, :size, :cycle, :base, :surge, :pri, TRUE, :now
                )
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "code": code,
                "name": name,
                "nid": nid,
                "size": size,
                "cycle": cycle,
                "base": base,
                "surge": surge,
                "pri": 10 if nid else 50,
                "now": now,
            },
        )
        counts["pricing_rules"] += 1

    inv = db.execute(
        text(
            """
            SELECT id, contract_id, amount_cents, currency
            FROM rental_billing_invoices
            WHERE status = 'OVERDUE' LIMIT 1
            """
        )
    ).mappings().first()
    if not inv:
        inv_id = str(uuid.uuid4())
        db.execute(
            text(
                """
                INSERT INTO rental_billing_invoices (
                    id, contract_id, invoice_number, period_start, period_end,
                    amount_cents, currency, status, due_at, created_at, updated_at
                ) VALUES (
                    :id, :cid, :num, :start, :end, :amt, 'BRL', 'OVERDUE', :due, :now, :now
                )
                """
            ),
            {
                "id": inv_id,
                "cid": cid,
                "num": f"RNT-OVD-{cid[:6].upper()}",
                "start": now - timedelta(days=60),
                "end": now - timedelta(days=30),
                "amt": int(contract["amount_cents"]),
                "due": now - timedelta(days=10),
                "now": now,
            },
        )
        inv = {"id": inv_id, "contract_id": cid, "amount_cents": contract["amount_cents"], "currency": "BRL"}

    if inv and not db.execute(
        text("SELECT id FROM rental_dunning_cases WHERE invoice_id = :i"),
        {"i": str(inv["id"])},
    ).mappings().first():
        db.execute(
            text(
                """
                INSERT INTO rental_dunning_cases (
                    id, contract_id, invoice_id, stage, amount_due_cents, currency,
                    status, next_action_at, created_at, updated_at
                ) VALUES (
                    :id, :cid, :iid, 'REMINDER_2', :amt, :cur, 'OPEN', :next, :now, :now
                )
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "cid": str(inv["contract_id"]),
                "iid": str(inv["id"]),
                "amt": int(inv["amount_cents"]),
                "cur": str(inv["currency"]),
                "next": now + timedelta(days=2),
                "now": now,
            },
        )
        counts["dunning"] += 1

    pending = db.execute(
        text("SELECT id, locker_id, slot_label FROM rental_contracts WHERE status = 'PENDING' LIMIT 1")
    ).mappings().first()
    if pending and not db.execute(text("SELECT id FROM rental_transfer_requests LIMIT 1")).mappings().first():
        db.execute(
            text(
                """
                INSERT INTO rental_transfer_requests (
                    id, contract_id, from_locker_id, from_slot_label,
                    to_locker_id, to_slot_label, status, requested_by, created_at
                ) VALUES (
                    :id, :cid, :fl, :fs, :tl, :ts, 'REQUESTED', 'ops', :now
                )
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "cid": str(pending["id"]),
                "fl": pending["locker_id"],
                "fs": pending["slot_label"],
                "tl": lid,
                "ts": slot,
                "now": now,
            },
        )
        counts["transfers"] += 1

    return counts
