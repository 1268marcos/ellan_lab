from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import case
from sqlalchemy.orm import Session

from app.core.auth_dep import get_current_verified_public_user
from app.core.datetime_utils import to_iso_utc
from app.core.db import get_db
from app.models.credit import Credit, CreditStatus
from app.models.user import User
from app.schemas.orders import OnlineRegion
from app.services.credits_service import (
    checkout_wallet_currency_matches_order,
    get_user_wallet_currency,
    select_checkout_credit_candidate,
)

router = APIRouter(prefix="/public/me", tags=["public-me"])


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class PublicCreditItemOut(BaseModel):
    id: str
    order_id: str | None = None
    amount_cents: int
    status: str
    created_at: str | None = None
    expires_at: str | None = None
    used_at: str | None = None
    revoked_at: str | None = None
    source_type: str | None = None
    source_reason: str | None = None
    notes: str | None = None
    is_available_now: bool
    days_to_expiration: int | None = None


class PublicCreditsSummaryOut(BaseModel):
    available_balance_cents: int
    available_count: int
    expiring_soon_count: int
    currency: str | None = None


class PublicCreditsListOut(BaseModel):
    summary: PublicCreditsSummaryOut
    items: list[PublicCreditItemOut]


class PublicCreditCheckoutPreviewOut(BaseModel):
    eligible: bool
    reason: str
    requested_use_credit: bool
    base_amount_cents: int
    discount_cents: int
    final_amount_cents: int
    credit_id: str | None = None
    currency: str | None = None
    order_currency: str | None = None
    wallet_currency: str | None = None


def _order_currency_from_region(region: str) -> str:
    region_upper = str(region or "").strip().upper()
    try:
        return OnlineRegion.get_currency(OnlineRegion(region_upper))
    except Exception:
        return "BRL"


@router.get("/credits", response_model=PublicCreditsListOut)
def list_my_credits(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_public_user),
):
    now = _utc_now()

    credits = (
        db.query(Credit)
        .filter(Credit.user_id == current_user.id)
        .order_by(
            case((Credit.status == CreditStatus.AVAILABLE, 0), else_=1),
            Credit.expires_at.asc(),
            Credit.created_at.desc(),
        )
        .all()
    )

    available_credits = [c for c in credits if c.is_available_now(now=now)]
    available_balance_cents = sum(int(c.amount_cents or 0) for c in available_credits)

    expiring_soon_count = 0
    items: list[PublicCreditItemOut] = []
    for credit in credits:
        expires_at = credit.expires_at
        expires_at_utc = None
        if expires_at is not None:
            expires_at_utc = expires_at if expires_at.tzinfo else expires_at.replace(tzinfo=timezone.utc)

        days_to_expiration = None
        if expires_at_utc is not None:
            delta = expires_at_utc - now
            days_to_expiration = max(delta.days, 0) if delta.total_seconds() >= 0 else 0

        is_available_now = credit.is_available_now(now=now)
        if is_available_now and expires_at_utc is not None:
            if 0 <= (expires_at_utc - now).total_seconds() <= (7 * 24 * 60 * 60):
                expiring_soon_count += 1

        items.append(
            PublicCreditItemOut(
                id=credit.id,
                order_id=credit.order_id,
                amount_cents=int(credit.amount_cents or 0),
                status=getattr(credit.status, "value", str(credit.status)),
                created_at=to_iso_utc(credit.created_at),
                expires_at=to_iso_utc(credit.expires_at),
                used_at=to_iso_utc(credit.used_at),
                revoked_at=to_iso_utc(credit.revoked_at),
                source_type=credit.source_type,
                source_reason=credit.source_reason,
                notes=credit.notes,
                is_available_now=is_available_now,
                days_to_expiration=days_to_expiration,
            )
        )

    wallet_currency = get_user_wallet_currency(db, user_id=current_user.id)

    return PublicCreditsListOut(
        summary=PublicCreditsSummaryOut(
            available_balance_cents=available_balance_cents,
            available_count=len(available_credits),
            expiring_soon_count=expiring_soon_count,
            currency=wallet_currency,
        ),
        items=items,
    )


@router.get("/credits/checkout-preview", response_model=PublicCreditCheckoutPreviewOut)
def preview_checkout_credit(
    amount_cents: int = Query(..., gt=0),
    use_credit: bool = Query(default=False),
    credit_id: str | None = Query(default=None),
    region: str = Query(default="SP", min_length=2, max_length=8),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_public_user),
):
    base_amount = int(amount_cents or 0)
    wallet_currency = get_user_wallet_currency(db, user_id=current_user.id)
    order_currency = _order_currency_from_region(region)

    if not use_credit:
        return PublicCreditCheckoutPreviewOut(
            eligible=False,
            reason="not_requested",
            requested_use_credit=False,
            base_amount_cents=base_amount,
            discount_cents=0,
            final_amount_cents=base_amount,
            credit_id=None,
            currency=wallet_currency,
            order_currency=order_currency,
            wallet_currency=wallet_currency,
        )

    if not checkout_wallet_currency_matches_order(
        wallet_currency=wallet_currency,
        order_currency=order_currency,
    ):
        return PublicCreditCheckoutPreviewOut(
            eligible=False,
            reason="currency_mismatch",
            requested_use_credit=True,
            base_amount_cents=base_amount,
            discount_cents=0,
            final_amount_cents=base_amount,
            credit_id=None,
            currency=wallet_currency,
            order_currency=order_currency,
            wallet_currency=wallet_currency,
        )

    credit = select_checkout_credit_candidate(
        db=db,
        user_id=current_user.id,
        order_amount_cents=base_amount,
        requested_credit_id=credit_id,
        lock_for_update=False,
    )
    if credit is None:
        return PublicCreditCheckoutPreviewOut(
            eligible=False,
            reason="no_eligible_credit",
            requested_use_credit=True,
            base_amount_cents=base_amount,
            discount_cents=0,
            final_amount_cents=base_amount,
            credit_id=None,
            currency=wallet_currency,
            order_currency=order_currency,
            wallet_currency=wallet_currency,
        )

    discount_cents = int(credit.amount_cents or 0)
    final_amount_cents = max(base_amount - discount_cents, 1)
    return PublicCreditCheckoutPreviewOut(
        eligible=True,
        reason="eligible",
        requested_use_credit=True,
        base_amount_cents=base_amount,
        discount_cents=discount_cents,
        final_amount_cents=final_amount_cents,
        credit_id=credit.id,
        currency=wallet_currency or order_currency,
        order_currency=order_currency,
        wallet_currency=wallet_currency,
    )
