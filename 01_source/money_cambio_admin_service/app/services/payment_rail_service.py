from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.advanced import MoneyPlayerPaymentRail
from app.schemas.advanced import PaymentRailIn
from app.services.crypto_util import new_id


def list_rails(
    db: Session,
    *,
    player_code: str | None = None,
    country_code: str | None = None,
    enabled_only: bool = False,
) -> list[MoneyPlayerPaymentRail]:
    q = db.query(MoneyPlayerPaymentRail)
    if player_code:
        q = q.filter(MoneyPlayerPaymentRail.player_code == player_code.upper())
    if country_code:
        q = q.filter(MoneyPlayerPaymentRail.country_code == country_code.upper())
    if enabled_only:
        q = q.filter(MoneyPlayerPaymentRail.is_enabled.is_(True))
    return q.order_by(
        MoneyPlayerPaymentRail.player_code,
        MoneyPlayerPaymentRail.country_code,
    ).all()


def create_rail(db: Session, body: PaymentRailIn) -> MoneyPlayerPaymentRail:
    pc = body.player_code.upper()
    cc = body.country_code.upper()
    pm = body.payment_method_code.upper() if body.payment_method_code else None
    wp = body.wallet_provider_code.upper() if body.wallet_provider_code else None
    ch = body.channel.upper()
    exists = (
        db.query(MoneyPlayerPaymentRail)
        .filter(
            MoneyPlayerPaymentRail.player_code == pc,
            MoneyPlayerPaymentRail.country_code == cc,
            MoneyPlayerPaymentRail.payment_method_code == pm,
            MoneyPlayerPaymentRail.wallet_provider_code == wp,
            MoneyPlayerPaymentRail.channel == ch,
        )
        .first()
    )
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="rail_exists")
    row = MoneyPlayerPaymentRail(
        id=new_id(),
        player_code=pc,
        country_code=cc,
        payment_method_code=pm,
        wallet_provider_code=wp,
        channel=ch,
        is_enabled=body.is_enabled,
        max_amount_cents=body.max_amount_cents,
        notes=body.notes,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
