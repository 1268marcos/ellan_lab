from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import uuid4

from sqlalchemy import text

from app.core.db import SessionLocal


@dataclass(frozen=True)
class EcommercePartnerSeed:
    id: str
    name: str
    code: str
    integration_type: str
    revenue_share_pct: float
    country: str
    tier: str
    status: str
    currency: str = "BRL"
    sla_pickup_hours: int = 72
    active: bool = True
    partner_type: str = "ECOMMERCE"


PARTNERS: tuple[EcommercePartnerSeed, ...] = (
    EcommercePartnerSeed(
        id="OP-ELLAN-001",
        name="Ellan Operacoes",
        code="ELLAN",
        integration_type="DIRECT",
        revenue_share_pct=0.15,
        country="BR",
        tier="PREMIUM",
        status="ACTIVE",
        currency="BRL",
        sla_pickup_hours=72,
    ),
    EcommercePartnerSeed(
        id="OP-PHARMA-001",
        name="Rede Farmacias",
        code="PHARMA",
        integration_type="WEBHOOK",
        revenue_share_pct=0.12,
        country="PT",
        tier="STANDARD",
        status="ACTIVE",
        currency="EUR",
        sla_pickup_hours=48,
    ),
)


def _upsert_ecommerce_partner(db, partner: EcommercePartnerSeed) -> None:
    existing = db.execute(
        text("SELECT id FROM ecommerce_partners WHERE id = :id"),
        {"id": partner.id},
    ).fetchone()

    payload = {
        "id": partner.id,
        "name": partner.name,
        "code": partner.code,
        "integration_type": partner.integration_type,
        "revenue_share_pct": partner.revenue_share_pct,
        "country": partner.country,
        "tier": partner.tier,
        "status": partner.status,
        "currency": partner.currency,
        "sla_pickup_hours": partner.sla_pickup_hours,
        "active": partner.active,
    }

    if existing:
        db.execute(
            text(
                """
                UPDATE ecommerce_partners
                SET
                    name = :name,
                    code = :code,
                    integration_type = :integration_type,
                    revenue_share_pct = :revenue_share_pct,
                    country = :country,
                    tier = :tier,
                    status = :status,
                    currency = :currency,
                    sla_pickup_hours = :sla_pickup_hours,
                    active = :active,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :id
                """
            ),
            payload,
        )
        return

    db.execute(
        text(
            """
            INSERT INTO ecommerce_partners (
                id,
                name,
                code,
                integration_type,
                revenue_share_pct,
                country,
                tier,
                status,
                currency,
                sla_pickup_hours,
                active
            ) VALUES (
                :id,
                :name,
                :code,
                :integration_type,
                :revenue_share_pct,
                :country,
                :tier,
                :status,
                :currency,
                :sla_pickup_hours,
                :active
            )
            """
        ),
        payload,
    )


def _materialize_locker_slots(db) -> tuple[int, int]:
    configs = db.execute(
        text(
            """
            SELECT locker_id, slot_size, slot_count
            FROM locker_slot_configs
            WHERE slot_count > 0
            ORDER BY locker_id, slot_size
            """
        )
    ).mappings().all()

    created = 0
    touched_lockers: set[str] = set()

    for row in configs:
        locker_id = str(row["locker_id"])
        slot_size = str(row["slot_size"])
        slot_count = int(row["slot_count"] or 0)
        touched_lockers.add(locker_id)

        for idx in range(1, slot_count + 1):
            slot_label = f"{slot_size}-{idx}"
            exists = db.execute(
                text(
                    """
                    SELECT 1
                    FROM locker_slots
                    WHERE locker_id = :locker_id
                      AND slot_label = :slot_label
                    """
                ),
                {"locker_id": locker_id, "slot_label": slot_label},
            ).fetchone()
            if exists:
                continue

            db.execute(
                text(
                    """
                    INSERT INTO locker_slots (
                        id, locker_id, slot_label, slot_size, status
                    ) VALUES (
                        :id, :locker_id, :slot_label, :slot_size, 'AVAILABLE'
                    )
                    """
                ),
                {
                    "id": str(uuid4()),
                    "locker_id": locker_id,
                    "slot_label": slot_label,
                    "slot_size": slot_size,
                },
            )
            created += 1

    for locker_id in touched_lockers:
        counts = db.execute(
            text(
                """
                SELECT
                    COUNT(*) AS total_slots,
                    COUNT(*) FILTER (WHERE status = 'AVAILABLE') AS available_slots
                FROM locker_slots
                WHERE locker_id = :locker_id
                """
            ),
            {"locker_id": locker_id},
        ).mappings().first()

        if not counts:
            continue

        db.execute(
            text(
                """
                UPDATE lockers
                SET
                    slots_count = :slots_count,
                    slots_available = :slots_available,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :locker_id
                """
            ),
            {
                "locker_id": locker_id,
                "slots_count": int(counts["total_slots"] or 0),
                "slots_available": int(counts["available_slots"] or 0),
            },
        )

    return created, len(touched_lockers)


def _upsert_partner_service_areas(db, today: date) -> tuple[int, int]:
    inserted = 0
    reactivated = 0

    partner_rows = db.execute(
        text("SELECT id, country FROM ecommerce_partners WHERE active IS TRUE")
    ).mappings().all()

    for partner in partner_rows:
        partner_id = str(partner["id"])
        country = str(partner["country"] or "").upper()
        is_pharma = partner_id == "OP-PHARMA-001"

        if is_pharma:
            candidate = db.execute(
                text(
                    """
                    SELECT id
                    FROM lockers
                    WHERE active IS TRUE
                      AND country = :country
                    ORDER BY security_level DESC, id ASC
                    LIMIT 1
                    """
                ),
                {"country": country},
            ).fetchone()
            locker_ids = [str(candidate[0])] if candidate else []
        else:
            locker_ids = [
                str(row[0])
                for row in db.execute(
                    text(
                        """
                        SELECT id
                        FROM lockers
                        WHERE active IS TRUE
                          AND country = :country
                        ORDER BY id
                        """
                    ),
                    {"country": country},
                ).fetchall()
            ]

        for locker_id in locker_ids:
            existing = db.execute(
                text(
                    """
                    SELECT id, is_active
                    FROM partner_service_areas
                    WHERE partner_id = :partner_id
                      AND locker_id = :locker_id
                    ORDER BY created_at DESC
                    LIMIT 1
                    """
                ),
                {"partner_id": partner_id, "locker_id": locker_id},
            ).mappings().first()

            if existing:
                if not bool(existing["is_active"]):
                    db.execute(
                        text(
                            """
                            UPDATE partner_service_areas
                            SET
                                is_active = TRUE,
                                valid_from = :valid_from,
                                valid_until = NULL
                            WHERE id = :id
                            """
                        ),
                        {"id": str(existing["id"]), "valid_from": today},
                    )
                    reactivated += 1
                continue

            db.execute(
                text(
                    """
                    INSERT INTO partner_service_areas (
                        id,
                        partner_id,
                        partner_type,
                        locker_id,
                        priority,
                        exclusive,
                        valid_from,
                        is_active
                    ) VALUES (
                        :id,
                        :partner_id,
                        :partner_type,
                        :locker_id,
                        :priority,
                        :exclusive,
                        :valid_from,
                        TRUE
                    )
                    """
                ),
                {
                    "id": str(uuid4()),
                    "partner_id": partner_id,
                    "partner_type": "ECOMMERCE",
                    "locker_id": locker_id,
                    "priority": 200 if is_pharma else 100,
                    "exclusive": is_pharma,
                    "valid_from": today,
                },
            )
            inserted += 1

    return inserted, reactivated


def run() -> None:
    db = SessionLocal()
    today = date.today()
    try:
        for partner in PARTNERS:
            _upsert_ecommerce_partner(db, partner)

        slots_created, touched_lockers = _materialize_locker_slots(db)
        psa_inserted, psa_reactivated = _upsert_partner_service_areas(db, today)

        db.commit()
        print(
            (
                "Sprint 0 seed concluido | "
                f"partners_upserted={len(PARTNERS)} | "
                f"slots_created={slots_created} | "
                f"lockers_touched={touched_lockers} | "
                f"psa_inserted={psa_inserted} | "
                f"psa_reactivated={psa_reactivated}"
            )
        )
    finally:
        db.close()


if __name__ == "__main__":
    run()
