from __future__ import annotations

import hashlib
import os

from sqlalchemy.orm import Session

from app.models.partner import Partner, PartnerApiKey

DEV_PARTNERS: list[dict[str, str]] = [
    {
        "id": "ellan-ceo-dev-hub-000000000",
        "name": "Ellan CEO Dev Hub",
        "role": "admin",
        "api_key": "pk_local_dev_key_ceo_01",
    },
    {
        "id": "ellan-coo-dev-hub-000000000",
        "name": "Ellan COO Dev Hub",
        "role": "ops",
        "api_key": "pk_local_dev_key_coo_01",
    },
    {
        "id": "11111111-1111-1111-1111-111111111111",
        "name": "Partner Demo Frontend",
        "role": "partner",
        "api_key": "pk_test_frontend_v1_20260505",
    },
]


def _hash_api_key(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def seed_dev_partners(db: Session) -> None:
    if os.getenv("SEED_DEV_PARTNERS", "true").strip().lower() in {"0", "false", "no"}:
        return

    for row in DEV_PARTNERS:
        partner = db.query(Partner).filter(Partner.id == row["id"]).first()
        if not partner:
            partner = Partner(
                id=row["id"],
                name=row["name"],
                partner_type="ECOMMERCE",
                status="ACTIVE",
            )
            db.add(partner)
            db.flush()

        key_hash = _hash_api_key(row["api_key"])
        prefix = row["api_key"][:12]
        existing = (
            db.query(PartnerApiKey)
            .filter(
                PartnerApiKey.partner_id == partner.id,
                PartnerApiKey.key_hash == key_hash,
            )
            .first()
        )
        if not existing:
            db.add(
                PartnerApiKey(
                    partner_id=partner.id,
                    key_hash=key_hash,
                    key_prefix=prefix,
                    is_active=True,
                )
            )

    db.commit()
