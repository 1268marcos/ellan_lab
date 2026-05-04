from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.product import Product
from app.schemas.compatibility import (
    CompatibilityOut,
    LockerCompatibilityCheckIn,
    ProductCompatibilityCheckIn,
)
from app.services import compatibility_service

router = APIRouter(tags=["compatibility"])


@router.post("/partners/{partner_id}/check-compatibility", response_model=CompatibilityOut)
def check_by_partner_sku(
    partner_id: str,
    body: ProductCompatibilityCheckIn,
    db: Session = Depends(get_db),
) -> CompatibilityOut:
    p = (
        db.query(Product)
        .filter(Product.partner_id == partner_id, Product.partner_sku == body.partner_sku)
        .first()
    )
    if not p:
        return CompatibilityOut(compatible=False, reason="PRODUCT_NOT_REGISTERED", recommended_slot_size=None)
    locker = compatibility_service.get_locker(db, body.locker_id)
    res = compatibility_service.is_product_compatible_with_locker(db, p, locker=locker, locker_spec=None)
    reason = res.reason
    if res.failed_messages and not reason:
        reason = res.failed_messages[0]
    return CompatibilityOut(compatible=res.compatible, reason=reason, recommended_slot_size=res.recommended_slot_size)


@router.post("/products/{sku_id}/check-compatibility", response_model=CompatibilityOut)
def check_by_sku(
    sku_id: str,
    body: LockerCompatibilityCheckIn,
    db: Session = Depends(get_db),
) -> CompatibilityOut:
    p = db.query(Product).filter(Product.sku_id == sku_id).first()
    if not p:
        return CompatibilityOut(compatible=False, reason="PRODUCT_NOT_REGISTERED", recommended_slot_size=None)
    spec = body.locker_spec.model_dump()
    res = compatibility_service.is_product_compatible_with_locker(db, p, locker=None, locker_spec=spec)
    reason = res.reason if not res.compatible else None
    return CompatibilityOut(compatible=res.compatible, reason=reason, recommended_slot_size=res.recommended_slot_size)
