from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import secrets
import uuid
from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.metrics import shadow_comparisons_total, shadow_divergences_total
from app.models.partner import Partner, PartnerApiKey
from app.schemas.partner import PartnerCreate, PartnerOut, PartnerPublicDict

logger = logging.getLogger(__name__)

PARTNER_GET_PUBLIC_FIELDS = frozenset(PartnerPublicDict.model_fields.keys())


def _hash_key(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def _gen_api_key() -> str:
    return f"pk_{secrets.token_urlsafe(32)}"


def create_partner(db: Session, body: PartnerCreate) -> tuple[Partner, str]:
    partner = Partner(
        id=str(uuid.uuid4()),
        name=body.name,
        partner_type=body.partner_type,
        legal_name=body.legal_name,
        contact_email=str(body.contact_email) if body.contact_email else None,
        status=body.status,
    )
    raw_key = _gen_api_key()
    key = PartnerApiKey(
        id=str(uuid.uuid4()),
        partner_id=partner.id,
        key_hash=_hash_key(raw_key),
        key_prefix=raw_key[:8],
        is_active=True,
    )
    db.add(partner)
    db.add(key)
    db.commit()
    db.refresh(partner)
    return partner, raw_key


def get_partner(db: Session, partner_id: str) -> Partner | None:
    return db.query(Partner).filter(Partner.id == partner_id).first()


def partner_to_out(p: Partner) -> PartnerOut:
    return PartnerOut.model_validate(p)


def partner_to_public_dict(p: Partner) -> dict[str, Any]:
    return PartnerPublicDict(
        id=p.id,
        name=p.name,
        partner_type=p.partner_type,
        legal_name=p.legal_name,
        contact_email=p.contact_email,
        status=p.status,
        created_at=p.created_at,
        updated_at=p.updated_at,
    ).model_dump(mode="json")


def rotate_api_key(db: Session, partner_id: str) -> tuple[str, str] | None:
    partner = get_partner(db, partner_id)
    if not partner:
        return None
    for k in partner.api_keys:
        k.is_active = False
    raw_key = _gen_api_key()
    nk = PartnerApiKey(
        id=str(uuid.uuid4()),
        partner_id=partner_id,
        key_hash=_hash_key(raw_key),
        key_prefix=raw_key[:8],
        is_active=True,
    )
    db.add(nk)
    db.commit()
    return raw_key, nk.key_prefix


def compare_public_schema(local: dict[str, Any], remote: dict[str, Any]) -> list[str]:
    divergences: list[str] = []
    for field in PARTNER_GET_PUBLIC_FIELDS:
        if field not in remote:
            divergences.append(f"missing_remote:{field}")
            continue
        if field not in local:
            divergences.append(f"missing_local:{field}")
            continue
        if remote[field] != local[field]:
            divergences.append(f"mismatch:{field}")
    return divergences


async def run_shadow_partner_compare(partner_id: str, local_payload: dict[str, Any]) -> None:
    settings = get_settings()
    if not settings.shadow_mode_enabled or not settings.shadow_legacy_base_url:
        return
    url = f"{settings.shadow_legacy_base_url.rstrip('/')}/partners/{partner_id}"
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(url)
            remote = resp.json()
    except Exception as exc:
        logger.warning("shadow_legacy_fetch_failed partner_id=%s err=%s", partner_id, exc)
        return
    if not isinstance(remote, dict):
        logger.warning("shadow_legacy_invalid_json_type partner_id=%s", partner_id)
        shadow_comparisons_total.inc()
        shadow_divergences_total.labels(partner_id=partner_id).inc()
        return
    shadow_comparisons_total.inc()
    divs = compare_public_schema(local_payload, remote)
    if divs:
        shadow_divergences_total.labels(partner_id=partner_id).inc()
        logger.warning("shadow_divergence partner_id=%s %s", partner_id, json.dumps(divs))


def schedule_shadow_compare(partner_id: str, local_payload: dict[str, Any]) -> None:
    settings = get_settings()
    if not settings.shadow_mode_enabled or not settings.shadow_legacy_base_url:
        return
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return
    loop.create_task(run_shadow_partner_compare(partner_id, local_payload))


def eligible_lockers_for_partner(partner_id: str, product_sku: str | None) -> dict[str, Any]:
    base = [
        {
            "id": "locker-m-001",
            "site_id": "site-sp-001",
            "slot_size": "M",
            "max_weight_g": 5000,
        },
        {
            "id": "locker-l-002",
            "site_id": "site-sp-001",
            "slot_size": "L",
            "max_weight_g": 12000,
        },
    ]
    if product_sku == "HEAVY_ONLY":
        base = [b for b in base if b["slot_size"] == "L"]
    return {"partner_id": partner_id, "product_sku": product_sku, "lockers": base}


def check_compatibility_stub(partner_id: str, partner_sku: str, locker_id: str) -> dict[str, Any]:
    if partner_sku == "UNKNOWN_SKU":
        return {"compatible": False, "reason": "PRODUCT_NOT_REGISTERED", "recommended_slot_size": None}
    valid_lockers = {"locker-m-001", "locker-l-002"}
    if locker_id not in valid_lockers:
        return {"compatible": False, "reason": "LOCKER_NOT_FOUND", "recommended_slot_size": None}
    if partner_sku == "OVERSIZE":
        return {"compatible": False, "reason": "SLOT_TOO_SMALL", "recommended_slot_size": "XL"}
    return {"compatible": True, "reason": None, "recommended_slot_size": "M"}
