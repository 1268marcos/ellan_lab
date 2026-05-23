"""Seed de planos e contratos de aluguel (rental_plans / rental_contracts)."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.rental_locker_ecosystem import (
    LOCKER_ECOSYSTEM_CORRIDORS,
    LOCKER_ECOSYSTEM_NETWORKS,
    LOCKER_ECOSYSTEM_OPERATORS,
    LOCKER_ECOSYSTEM_PLANS,
    LOCKER_ECOSYSTEM_SLA,
    LOCKER_ECOSYSTEM_WEBHOOK_TENANTS,
)

_WEBHOOK_EVENTS = [
    "rental.contract.created",
    "rental.contract.activated",
    "rental.contract.cancelled",
    "rental.billing.due",
]

_PLAN_NETWORK_LINKS = [(p["id"], p["network_id"]) for p in LOCKER_ECOSYSTEM_PLANS if p.get("network_id")]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _upsert_network(db: Session, n: dict, now: datetime) -> str:
    """Insere ou atualiza metadados da rede (complemento idempotente)."""
    row = db.execute(
        text("SELECT id FROM rental_networks WHERE id = :id OR code = :code LIMIT 1"),
        {"id": n["id"], "code": n["code"]},
    ).mappings().first()
    countries = json.dumps(n.get("countries") or [])
    payload = {
        "id": n["id"],
        "code": n["code"],
        "name": n["name"],
        "network_type": n["network_type"],
        "hardware_vendor": n.get("hardware_vendor"),
        "countries": countries,
        "website_url": n.get("website_url"),
        "now": now,
    }
    if row:
        db.execute(
            text(
                """
                UPDATE rental_networks SET
                    name = :name, network_type = :network_type, hardware_vendor = :hardware_vendor,
                    primary_countries_json = :countries, website_url = :website_url,
                    active = TRUE, updated_at = :now
                WHERE id = :id OR code = :code
                """
            ),
            payload,
        )
        return "updated"
    db.execute(
        text(
            """
            INSERT INTO rental_networks (
                id, code, name, network_type, hardware_vendor, primary_countries_json,
                website_url, active, created_at, updated_at
            ) VALUES (
                :id, :code, :name, :network_type, :hardware_vendor, :countries,
                :website_url, TRUE, :now, :now
            )
            """
        ),
        payload,
    )
    return "created"


def seed_rental_professional_tables(db: Session) -> dict[str, int]:
    """Redes mundiais, corredores, operadores, SLA e faturas demo."""
    now = _now()
    nets_created = 0
    nets_updated = 0
    for n in LOCKER_ECOSYSTEM_NETWORKS:
        action = _upsert_network(db, n, now)
        if action == "created":
            nets_created += 1
        else:
            nets_updated += 1

    corridors = 0
    for network_id, origin, dest, sla, currency in LOCKER_ECOSYSTEM_CORRIDORS:
        exists = db.execute(
            text(
                """
                SELECT id FROM rental_network_corridors
                WHERE network_id = :nid AND origin_country = :o AND destination_country = :d
                """
            ),
            {"nid": network_id, "o": origin, "d": dest},
        ).mappings().first()
        if exists:
            continue
        db.execute(
            text(
                """
                INSERT INTO rental_network_corridors (
                    id, network_id, origin_country, destination_country, sla_hours, currency, active, created_at
                ) VALUES (:id, :nid, :o, :d, :sla, :currency, TRUE, :now)
                """
            ),
            {"id": str(uuid.uuid4()), "nid": network_id, "o": origin, "d": dest, "sla": sla, "currency": currency, "now": now},
        )
        corridors += 1

    operators = 0
    for op in LOCKER_ECOSYSTEM_OPERATORS:
        if db.execute(text("SELECT id FROM rental_operators WHERE id = :id"), {"id": op["id"]}).mappings().first():
            db.execute(
                text(
                    """
                    UPDATE rental_operators SET
                        tenant_id = :tenant_id, network_id = :network_id, legal_name = :legal_name,
                        operator_code = :operator_code, commission_bps = :commission_bps,
                        status = 'ACTIVE', updated_at = :now
                    WHERE id = :id
                    """
                ),
                {**op, "now": now},
            )
            continue
        db.execute(
            text(
                """
                INSERT INTO rental_operators (
                    id, tenant_id, network_id, legal_name, operator_code,
                    commission_bps, status, created_at, updated_at
                ) VALUES (
                    :id, :tenant_id, :network_id, :legal_name, :operator_code,
                    :commission_bps, 'ACTIVE', :now, :now
                )
                """
            ),
            {**op, "now": now},
        )
        operators += 1

    sla_count = 0
    for network_id, metric, target, unit, penalty in LOCKER_ECOSYSTEM_SLA:
        exists = db.execute(
            text("SELECT id FROM rental_sla_policies WHERE network_id = :n AND metric_code = :m"),
            {"n": network_id, "m": metric},
        ).mappings().first()
        if exists:
            continue
        db.execute(
            text(
                """
                INSERT INTO rental_sla_policies (
                    id, network_id, metric_code, target_value, unit, breach_penalty_bps, active, created_at
                ) VALUES (:id, :n, :m, :t, :u, :p, TRUE, :now)
                """
            ),
            {"id": str(uuid.uuid4()), "n": network_id, "m": metric, "t": target, "u": unit, "p": penalty, "now": now},
        )
        sla_count += 1

    invoices = 0
    contract = db.execute(
        text("SELECT id, amount_cents FROM rental_contracts WHERE status = 'ACTIVE' LIMIT 1")
    ).mappings().first()
    if contract:
        cid = str(contract["id"])
        if not db.execute(
            text("SELECT id FROM rental_billing_invoices WHERE contract_id = :c LIMIT 1"),
            {"c": cid},
        ).mappings().first():
            db.execute(
                text(
                    """
                    INSERT INTO rental_billing_invoices (
                        id, contract_id, invoice_number, period_start, period_end,
                        amount_cents, currency, status, due_at, paid_at, created_at, updated_at
                    ) VALUES (
                        :id, :cid, :num, :start, :end, :amount, 'BRL', 'PAID', :due, :paid, :now, :now
                    )
                    """
                ),
                {
                    "id": str(uuid.uuid4()),
                    "cid": cid,
                    "num": f"RNT-SEED-{cid[:6].upper()}",
                    "start": now - timedelta(days=30),
                    "end": now,
                    "amount": int(contract["amount_cents"]),
                    "due": now - timedelta(days=5),
                    "paid": now - timedelta(days=1),
                    "now": now,
                },
            )
            invoices += 1

    deliveries = 0
    endpoint = db.execute(
        text("SELECT id FROM rental_webhook_endpoints WHERE tenant_id = 'tenant-inpost-br' LIMIT 1")
    ).mappings().first()
    if endpoint and contract:
        if not db.execute(text("SELECT id FROM rental_webhook_deliveries LIMIT 1")).mappings().first():
            db.execute(
                text(
                    """
                    INSERT INTO rental_webhook_deliveries (
                        id, endpoint_id, contract_id, event_type, status, attempt,
                        response_code, created_at
                    ) VALUES (
                        :id, :eid, :cid, 'rental.contract.activated', 'DELIVERED', 1, 200, :now
                    )
                    """
                ),
                {"id": str(uuid.uuid4()), "eid": str(endpoint["id"]), "cid": str(contract["id"]), "now": now},
            )
            deliveries += 1

    for plan_id, network_id in _PLAN_NETWORK_LINKS:
        db.execute(
            text("UPDATE rental_plans SET network_id = :nid WHERE id = :pid"),
            {"nid": network_id, "pid": plan_id},
        )

    db.execute(
        text(
            """
            UPDATE rental_contracts SET operator_id = 'op-inpost-br'
            WHERE id = 'rental-contract-demo-active' AND operator_id IS NULL
            """
        )
    )

    return {
        "networks": nets_created,
        "networks_updated": nets_updated,
        "corridors": corridors,
        "operators": operators,
        "sla_policies": sla_count,
        "invoices": invoices,
        "webhook_deliveries": deliveries,
    }


def seed_rental_integration_tables(db: Session) -> dict[str, int]:
    """Cria webhooks e API keys demo por tenant."""
    import hashlib

    created_wh = 0
    created_keys = 0
    now = _now()
    for tenant_id in LOCKER_ECOSYSTEM_WEBHOOK_TENANTS:
        row = db.execute(
            text("SELECT id FROM rental_webhook_endpoints WHERE tenant_id = :t LIMIT 1"),
            {"t": tenant_id},
        ).mappings().first()
        if not row:
            secret = f"whsec-{tenant_id}"
            db.execute(
                text(
                    """
                    INSERT INTO rental_webhook_endpoints (
                        id, tenant_id, url, secret_hash, events_json, active, created_at, updated_at
                    ) VALUES (
                        :id, :tenant_id, :url, :secret_hash, :events_json, TRUE, :now, :now
                    )
                    """
                ),
                {
                    "id": str(uuid.uuid4()),
                    "tenant_id": tenant_id,
                    "url": f"https://hooks.example.com/rentals/{tenant_id}",
                    "secret_hash": hashlib.sha256(secret.encode()).hexdigest(),
                    "events_json": json.dumps(_WEBHOOK_EVENTS),
                    "now": now,
                },
            )
            created_wh += 1
        key_row = db.execute(
            text("SELECT id FROM rental_api_keys WHERE tenant_id = :t AND revoked_at IS NULL LIMIT 1"),
            {"t": tenant_id},
        ).mappings().first()
        if not key_row:
            raw = f"rnt_{tenant_id}_demo_key"
            db.execute(
                text(
                    """
                    INSERT INTO rental_api_keys (
                        id, tenant_id, key_prefix, key_hash, label, scopes_json, created_at
                    ) VALUES (
                        :id, :tenant_id, :prefix, :key_hash, :label, :scopes, :now
                    )
                    """
                ),
                {
                    "id": str(uuid.uuid4()),
                    "tenant_id": tenant_id,
                    "prefix": raw[:12],
                    "key_hash": hashlib.sha256(raw.encode()).hexdigest(),
                    "label": "seed-demo",
                    "scopes": json.dumps(["rentals:read", "rentals:write", "rentals:webhook"]),
                    "now": now,
                },
            )
            created_keys += 1
    return {"webhooks": created_wh, "api_keys": created_keys}


def seed_rentals(db: Session) -> dict[str, int]:
    """Idempotente: catálogo mundial + contratos demo no primeiro locker disponível."""
    plans_created = 0
    plans_updated = 0
    now = _now()
    for p in LOCKER_ECOSYSTEM_PLANS:
        exists = db.execute(text("SELECT id FROM rental_plans WHERE id = :id"), {"id": p["id"]}).mappings().first()
        fields = {
            "id": p["id"],
            "locker_id": p.get("locker_id"),
            "slot_size": p.get("slot_size"),
            "name": p["name"],
            "description": p.get("description"),
            "billing_cycle": p["billing_cycle"],
            "amount_cents": p["amount_cents"],
            "network_id": p.get("network_id"),
            "now": now,
        }
        if exists:
            db.execute(
                text(
                    """
                    UPDATE rental_plans SET
                        name = :name, description = :description, billing_cycle = :billing_cycle,
                        amount_cents = :amount_cents, network_id = COALESCE(:network_id, network_id),
                        updated_at = :now, active = TRUE
                    WHERE id = :id
                    """
                ),
                fields,
            )
            plans_updated += 1
            continue
        db.execute(
            text(
                """
                INSERT INTO rental_plans (
                    id, locker_id, slot_size, name, description, billing_cycle,
                    amount_cents, currency, grace_period_hours, active, network_id, created_at, updated_at
                ) VALUES (
                    :id, :locker_id, :slot_size, :name, :description, :billing_cycle,
                    :amount_cents, 'BRL', 24, TRUE, :network_id, :now, :now
                )
                """
            ),
            fields,
        )
        plans_created += 1

    locker = db.execute(
        text("SELECT id FROM lockers WHERE active = TRUE ORDER BY created_at LIMIT 1")
    ).mappings().first()
    if not locker:
        integ = seed_rental_integration_tables(db)
        pro = seed_rental_professional_tables(db)
        db.commit()
        return {"plans": plans_created, "plans_updated": plans_updated, "contracts": 0, **integ, **pro}

    locker_id = str(locker["id"])
    db.execute(
        text(
            """
            UPDATE rental_plans SET locker_id = :locker_id
            WHERE id = 'rental-plan-inpost-m' AND locker_id IS NULL
            """
        ),
        {"locker_id": locker_id},
    )

    slot = db.execute(
        text(
            """
            SELECT slot_label FROM locker_slots
            WHERE locker_id = :lid ORDER BY slot_label LIMIT 1
            """
        ),
        {"lid": locker_id},
    ).mappings().first()
    slot_label = str(slot["slot_label"]) if slot else "01A"

    contracts_created = 0
    demos = [
        {
            "id": "rental-contract-demo-active",
            "status": "ACTIVE",
            "renter_name": "Operador InPost BR",
            "tenant_id": "tenant-inpost-br",
            "plan_id": "rental-plan-inpost-m",
            "operator_id": "op-inpost-br",
            "amount_cents": 14900,
            "billing_cycle": "MONTHLY",
            "next_billing_at": now + timedelta(days=28),
            "started_at": now - timedelta(days=2),
        },
        {
            "id": "rental-contract-demo-pending",
            "status": "PENDING",
            "renter_name": "Hub Magalu SP",
            "tenant_id": "tenant-magalu",
            "plan_id": "rental-plan-magalu-hub",
            "operator_id": "op-magalu",
            "amount_cents": 11900,
            "billing_cycle": "MONTHLY",
            "next_billing_at": None,
            "started_at": None,
        },
        {
            "id": "rental-contract-demo-correios",
            "status": "PENDING",
            "renter_name": "Correios Locker Piloto",
            "tenant_id": "tenant-correios-br",
            "plan_id": "rental-plan-correios-m",
            "operator_id": "op-correios-br",
            "amount_cents": 8900,
            "billing_cycle": "MONTHLY",
            "next_billing_at": None,
            "started_at": None,
        },
        {
            "id": "rental-contract-demo-amazon",
            "status": "PENDING",
            "renter_name": "Amazon Hub Locker BR",
            "tenant_id": "tenant-amazon-hub",
            "plan_id": "rental-plan-amazon-counter",
            "operator_id": "op-amazon-hub",
            "amount_cents": 15900,
            "billing_cycle": "MONTHLY",
            "next_billing_at": None,
            "started_at": None,
        },
    ]
    for c in demos:
        if db.execute(text("SELECT id FROM rental_contracts WHERE id = :id"), {"id": c["id"]}).mappings().first():
            continue
        db.execute(
            text(
                """
                INSERT INTO rental_contracts (
                    id, locker_id, slot_label, plan_id, tenant_id, renter_name, operator_id,
                    amount_cents, currency, billing_cycle, next_billing_at, auto_renew,
                    status, started_at, created_at, updated_at
                ) VALUES (
                    :id, :locker_id, :slot_label, :plan_id, :tenant_id, :renter_name, :operator_id,
                    :amount_cents, 'BRL', :billing_cycle, :next_billing_at, FALSE,
                    :status, :started_at, :now, :now
                )
                """
            ),
            {**c, "locker_id": locker_id, "slot_label": slot_label, "now": now},
        )
        if c["status"] == "ACTIVE":
            db.execute(
                text(
                    """
                    UPDATE locker_slots
                    SET status = 'RENTED', current_rental_id = :rid, updated_at = :now
                    WHERE locker_id = :lid AND slot_label = :slot
                    """
                ),
                {"rid": c["id"], "lid": locker_id, "slot": slot_label, "now": now},
            )
        contracts_created += 1

    integ = seed_rental_integration_tables(db)
    pro = seed_rental_professional_tables(db)
    from app.services.rental_events import log_rental_contract_event

    for cid in [d["id"] for d in demos]:
        if db.execute(text("SELECT id FROM rental_contracts WHERE id = :id"), {"id": cid}).mappings().first():
            if not db.execute(
                text("SELECT id FROM rental_contract_events WHERE contract_id = :c LIMIT 1"),
                {"c": cid},
            ).mappings().first():
                log_rental_contract_event(
                    db,
                    contract_id=cid,
                    event_type="contract.seeded",
                    payload={"source": "rental_locker_ecosystem"},
                    actor="seed",
                )
    db.commit()
    return {
        "plans": plans_created,
        "plans_updated": plans_updated,
        "contracts": contracts_created,
        **integ,
        **pro,
    }
