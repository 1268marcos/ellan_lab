from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.advanced import (
    FxLockIn,
    FxLockListOut,
    FxLockOut,
    PaymentRailIn,
    PaymentRailListOut,
    PaymentRailOut,
    PricingPreviewIn,
    PricingPreviewOut,
    TreasuryDashboardOut,
)
from app.services import fx_lock_service, payment_rail_service, pricing_service, treasury_service

router = APIRouter(tags=["advanced-ops"])


@router.post("/pricing/preview", response_model=PricingPreviewOut)
def pricing_preview(body: PricingPreviewIn, db: Session = Depends(get_db)) -> PricingPreviewOut:
    return pricing_service.preview_pricing(db, body)


@router.get("/payment-rails", response_model=PaymentRailListOut)
def list_payment_rails(
    player_code: str | None = None,
    country_code: str | None = None,
    enabled_only: bool = Query(False),
    db: Session = Depends(get_db),
) -> PaymentRailListOut:
    rows = payment_rail_service.list_rails(
        db, player_code=player_code, country_code=country_code, enabled_only=enabled_only
    )
    items = [PaymentRailOut.model_validate(r) for r in rows]
    return PaymentRailListOut(items=items, total=len(items))


@router.post("/payment-rails", response_model=PaymentRailOut, status_code=status.HTTP_201_CREATED)
def create_payment_rail(body: PaymentRailIn, db: Session = Depends(get_db)) -> PaymentRailOut:
    row = payment_rail_service.create_rail(db, body)
    return PaymentRailOut.model_validate(row)


@router.get("/treasury/dashboard", response_model=TreasuryDashboardOut)
def treasury_dashboard(db: Session = Depends(get_db)) -> TreasuryDashboardOut:
    return treasury_service.treasury_dashboard(db)


@router.get("/fx-locks", response_model=FxLockListOut)
def list_fx_locks(status: str | None = Query("ACTIVE"), db: Session = Depends(get_db)) -> FxLockListOut:
    rows = fx_lock_service.list_locks(db, status=status)
    items = [FxLockOut.model_validate(r) for r in rows]
    return FxLockListOut(items=items, total=len(items))


@router.post("/fx-locks", response_model=FxLockOut, status_code=status.HTTP_201_CREATED)
def create_fx_lock(body: FxLockIn, db: Session = Depends(get_db)) -> FxLockOut:
    row = fx_lock_service.create_lock(db, body)
    return FxLockOut.model_validate(row)
