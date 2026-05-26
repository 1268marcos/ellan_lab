from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.models.marketplace import MarketplaceCommission
from app.schemas.marketplace import CommissionCreateIn, CommissionNetPreviewOut, CommissionUpdateIn
from app.services.crypto_util import new_id
from app.services.seller_service import get_seller_or_404


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def preview_seller_net(db: Session, price_cents: int, commission_pct: Decimal) -> CommissionNetPreviewOut:
    if price_cents <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="price_cents_must_be_positive")
    try:
        row = db.execute(
            text(
                "SELECT commission_cents, ellan_fee_cents, gateway_fee_cents, net_cents "
                "FROM fn_calculate_seller_net(:price, :pct)"
            ),
            {"price": price_cents, "pct": commission_pct},
        ).mappings().first()
        if row:
            return CommissionNetPreviewOut(
                price_cents=price_cents,
                commission_pct=commission_pct,
                commission_cents=int(row["commission_cents"]),
                ellan_fee_cents=int(row["ellan_fee_cents"]),
                gateway_fee_cents=int(row["gateway_fee_cents"]),
                net_cents=int(row["net_cents"]),
            )
    except OperationalError:
        pass
    pct = float(commission_pct)
    commission_cents = round(price_cents * pct / 100)
    ellan_fee_cents = round(price_cents * 2.99 / 100)
    gateway_fee_cents = round(price_cents * 2.5 / 100)
    net_cents = price_cents - round(price_cents * (pct + 2.99 + 2.5) / 100)
    return CommissionNetPreviewOut(
        price_cents=price_cents,
        commission_pct=commission_pct,
        commission_cents=commission_cents,
        ellan_fee_cents=ellan_fee_cents,
        gateway_fee_cents=gateway_fee_cents,
        net_cents=net_cents,
    )


def list_commissions(
    db: Session,
    seller_id: str | None = None,
    status_filter: str | None = None,
) -> list[MarketplaceCommission]:
    q = db.query(MarketplaceCommission)
    if seller_id:
        q = q.filter(MarketplaceCommission.seller_id == seller_id)
    if status_filter:
        q = q.filter(MarketplaceCommission.status == status_filter)
    return q.order_by(MarketplaceCommission.created_at.desc()).all()


def get_commission_or_404(db: Session, commission_id: str) -> MarketplaceCommission:
    row = db.get(MarketplaceCommission, commission_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="commission_not_found")
    return row


def create_commission(db: Session, body: CommissionCreateIn) -> MarketplaceCommission:
    get_seller_or_404(db, body.seller_id)
    row = MarketplaceCommission(id=new_id(), created_at=_utcnow(), **body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_commission(db: Session, commission_id: str, body: CommissionUpdateIn) -> MarketplaceCommission:
    row = get_commission_or_404(db, commission_id)
    data = body.model_dump(exclude_unset=True)
    if data.get("status") == "SETTLED" and not data.get("settled_at"):
        data["settled_at"] = _utcnow()
    for k, v in data.items():
        setattr(row, k, v)
    db.commit()
    db.refresh(row)
    return row
