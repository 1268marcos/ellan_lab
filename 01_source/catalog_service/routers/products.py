from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from schemas import (
    CompatibilityCheckOut,
    EligibleLockerOut,
    LockerCheckIn,
    PartnerProductCreateIn,
    PartnerProductCreateOut,
    ProductDetailOut,
)
from services import catalog_service

partners_router = APIRouter(prefix="/partners", tags=["partners"])


@partners_router.post("/{partner_id}/products", response_model=PartnerProductCreateOut, status_code=201)
def post_partner_product(
    partner_id: str,
    payload: PartnerProductCreateIn,
    db: Session = Depends(get_db),
) -> PartnerProductCreateOut:
    product, _ = catalog_service.create_or_update_partner_product(db, partner_id, payload)
    return PartnerProductCreateOut(
        sku_id=product.sku_id,
        partner_id=product.partner_id,
        partner_sku=product.partner_sku,
    )


@partners_router.get("/{partner_id}/eligible-lockers", response_model=list[EligibleLockerOut])
def get_eligible_lockers(
    partner_id: str,
    product_sku: str | None = Query(default=None, alias="product_sku"),
    db: Session = Depends(get_db),
) -> list[EligibleLockerOut]:
    rows = catalog_service.list_eligible_lockers(db, partner_id, product_sku)
    return [EligibleLockerOut(**r) for r in rows]


products_router = APIRouter(tags=["products"])


@products_router.get("/products/{sku_id}", response_model=ProductDetailOut)
def get_product(sku_id: str, db: Session = Depends(get_db)) -> ProductDetailOut:
    return catalog_service.get_product_detail(db, sku_id)


@products_router.post(
    "/products/{sku_id}/check-compatibility",
    response_model=CompatibilityCheckOut,
)
def post_check_compatibility(
    sku_id: str,
    payload: LockerCheckIn,
    db: Session = Depends(get_db),
) -> CompatibilityCheckOut:
    res = catalog_service.check_product_compatibility(db, sku_id, payload)
    return CompatibilityCheckOut(
        compatible=res.compatible,
        reason=res.reason,
        recommended_slot_size=res.recommended_slot_size,
    )
