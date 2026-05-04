from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.compatibility import Locker, PartnerProductRule
from app.models.product import Product


@dataclass
class CompatibilityResult:
    compatible: bool
    reason: str | None = None
    recommended_slot_size: str | None = None
    failed_messages: list[str] | None = None


def _rule_for_partner(db: Session, partner_id: str, category_id: str | None) -> PartnerProductRule | None:
    q = db.query(PartnerProductRule).filter(PartnerProductRule.partner_id == partner_id)
    if category_id:
        q = q.filter(
            or_(PartnerProductRule.category_id == category_id, PartnerProductRule.category_id.is_(None))
        )
    return q.order_by(PartnerProductRule.overrides_global.desc()).first()


def _allowed_temperatures(rule: PartnerProductRule | None) -> set[str]:
    if not rule:
        return {"AMBIENT", "REFRIGERATED", "FROZEN"}
    try:
        arr = json.loads(rule.allowed_temperature_zones)
        return set(arr) if isinstance(arr, list) else {"AMBIENT"}
    except json.JSONDecodeError:
        return {"AMBIENT"}


def is_product_compatible_with_locker(
    db: Session,
    product: Product,
    *,
    locker: Locker | None,
    locker_spec: dict[str, Any] | None = None,
) -> CompatibilityResult:
    if locker is None and not locker_spec:
        return CompatibilityResult(False, reason="LOCKER_NOT_FOUND", recommended_slot_size=None)

    max_w = int(locker.max_weight_g) if locker else int(locker_spec.get("max_weight_g") or 0)
    slot = locker.slot_size if locker else str(locker_spec.get("slot_size") or "M")

    weight_g = product.dimensions.weight_g if product.dimensions and product.dimensions.weight_g else 0
    if weight_g > max_w:
        return CompatibilityResult(
            False,
            reason="WEIGHT_EXCEEDS_LOCKER",
            recommended_slot_size="XL" if slot != "XL" else "OVERSIZE",
            failed_messages=["weight"],
        )

    rule = _rule_for_partner(db, product.partner_id, product.category_id)
    allowed = _allowed_temperatures(rule)
    if product.temperature_zone not in allowed:
        return CompatibilityResult(False, reason="TEMPERATURE_NOT_ALLOWED", recommended_slot_size=None, failed_messages=["temp"])

    if rule and rule.max_weight_g is not None and weight_g > rule.max_weight_g:
        return CompatibilityResult(False, reason="RULE_WEIGHT_EXCEEDED", recommended_slot_size="L", failed_messages=["rule_weight"])

    if rule and rule.requires_signature is True and not product.requires_signature:
        return CompatibilityResult(False, reason="SIGNATURE_REQUIRED", recommended_slot_size=None)

    if rule and rule.is_hazardous_allowed is False and product.is_hazardous:
        return CompatibilityResult(False, reason="HAZARDOUS_NOT_ALLOWED", recommended_slot_size=None)

    if slot == "S" and weight_g > 2000:
        return CompatibilityResult(False, reason="SLOT_TOO_SMALL", recommended_slot_size="M")

    return CompatibilityResult(True, reason=None, recommended_slot_size=slot)


def get_locker(db: Session, locker_id: str) -> Locker | None:
    return db.query(Locker).filter(Locker.id == locker_id).first()


def eligible_lockers(db: Session, partner_id: str, product_sku: str | None) -> dict[str, Any]:
    q = db.query(Locker).filter(Locker.partner_id == partner_id)
    rows = q.all()
    lockers: list[dict[str, str | int]] = [
        {"id": r.id, "site_id": r.site_id, "slot_size": r.slot_size, "max_weight_g": r.max_weight_g} for r in rows
    ]
    if product_sku:
        p = (
            db.query(Product)
            .filter(Product.partner_id == partner_id, Product.partner_sku == product_sku)
            .first()
        )
        if p and p.dimensions and p.dimensions.weight_g:
            w = p.dimensions.weight_g
            lockers = [x for x in lockers if int(x["max_weight_g"]) >= w]
    return {"partner_id": partner_id, "product_sku": product_sku, "lockers": lockers}
