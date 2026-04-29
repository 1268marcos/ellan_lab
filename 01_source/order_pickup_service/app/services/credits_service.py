# 01_source/order_pickup_service/app/services/credits_service.py
# 21/04/2026 - emissão e expiração de crédito 50% por pickup expirado

from __future__ import annotations

import logging
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.credit import Credit, CreditStatus
from app.models.order import Order

logger = logging.getLogger(__name__)

EXPIRED_PICKUP_CREDIT_DAYS = 30


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class CreditGrantResult:
    created: bool
    credit_id: str | None
    amount_cents: int
    status: str | None
    reason: str
    expires_at: str | None


@dataclass
class CreditCheckoutApplication:
    requested: bool
    applied: bool
    reason: str
    credit_id: str | None
    discount_cents: int
    final_amount_cents: int
    currency: str | None


def _calculate_credit_amount_cents(order: Order, ratio: float = 0.5) -> int:
    amount_cents = int(getattr(order, "amount_cents", 0) or 0)
    if amount_cents <= 0:
        return 0
    granted = int(round(amount_cents * ratio))
    return max(granted, 0)


def get_credit_by_order_id(db: Session, *, order_id: str) -> Credit | None:
    return db.query(Credit).filter(Credit.order_id == order_id).first()


def get_user_wallet_currency(db: Session, *, user_id: str | None) -> str | None:
    if not user_id:
        return None

    try:
        return db.execute(
            text(
                """
                SELECT currency
                FROM public.user_wallets
                WHERE user_id = :user_id
                ORDER BY created_at DESC
                LIMIT 1
                """
            ),
            {"user_id": user_id},
        ).scalar()
    except SQLAlchemyError as exc:
        logger.warning(
            "get_user_wallet_currency_failed",
            extra={"user_id": user_id, "error_type": exc.__class__.__name__},
        )
        return None


def select_checkout_credit_candidate(
    *,
    db: Session,
    user_id: str | None,
    order_amount_cents: int,
    requested_credit_id: str | None = None,
    now: datetime | None = None,
    lock_for_update: bool = False,
) -> Credit | None:
    if not user_id:
        return None

    # Evita total zero no checkout atual (fluxo de pagamento ainda é obrigatório).
    max_discount_cents = int(order_amount_cents or 0) - 1
    if max_discount_cents <= 0:
        return None

    ref = now or _utc_now()

    query = (
        db.query(Credit)
        .filter(
            Credit.user_id == user_id,
            Credit.status == CreditStatus.AVAILABLE,
            Credit.expires_at > ref,
            Credit.used_at.is_(None),
            Credit.revoked_at.is_(None),
            Credit.amount_cents <= max_discount_cents,
        )
        .order_by(Credit.expires_at.asc(), Credit.created_at.asc())
    )

    if requested_credit_id:
        query = query.filter(Credit.id == requested_credit_id)

    if lock_for_update:
        query = query.with_for_update()

    return query.first()


def checkout_wallet_currency_matches_order(
    *,
    wallet_currency: str | None,
    order_currency: str | None,
) -> bool:
    """
    Quando existe carteira, a moeda dela deve bater com a moeda do pedido.
    Sem carteira, não bloqueia (compatível com ambientes sem user_wallets).
    """
    if not wallet_currency or not order_currency:
        return True
    return str(wallet_currency).strip().upper() == str(order_currency).strip().upper()


def apply_credit_for_checkout(
    *,
    db: Session,
    user_id: str | None,
    base_amount_cents: int,
    order_currency: str | None,
    order_id: str | None = None,
    use_credit: bool = False,
    requested_credit_id: str | None = None,
    now: datetime | None = None,
) -> CreditCheckoutApplication:
    base_amount = int(base_amount_cents or 0)
    if not use_credit:
        return CreditCheckoutApplication(
            requested=False,
            applied=False,
            reason="not_requested",
            credit_id=None,
            discount_cents=0,
            final_amount_cents=base_amount,
            currency=order_currency,
        )

    if not user_id:
        return CreditCheckoutApplication(
            requested=True,
            applied=False,
            reason="missing_user",
            credit_id=None,
            discount_cents=0,
            final_amount_cents=base_amount,
            currency=order_currency,
        )

    wallet_currency = get_user_wallet_currency(db, user_id=user_id)
    if not checkout_wallet_currency_matches_order(
        wallet_currency=wallet_currency,
        order_currency=order_currency,
    ):
        return CreditCheckoutApplication(
            requested=True,
            applied=False,
            reason="currency_mismatch",
            credit_id=None,
            discount_cents=0,
            final_amount_cents=base_amount,
            currency=wallet_currency,
        )

    ref = now or _utc_now()
    credit = select_checkout_credit_candidate(
        db=db,
        user_id=user_id,
        order_amount_cents=base_amount,
        requested_credit_id=requested_credit_id,
        now=ref,
        lock_for_update=True,
    )
    if credit is None:
        return CreditCheckoutApplication(
            requested=True,
            applied=False,
            reason="no_eligible_credit",
            credit_id=None,
            discount_cents=0,
            final_amount_cents=base_amount,
            currency=wallet_currency or order_currency,
        )

    discount_cents = int(credit.amount_cents or 0)
    final_amount_cents = max(base_amount - discount_cents, 1)

    credit.status = CreditStatus.USED
    credit.used_at = ref
    credit.updated_at = ref
    applied_note = (
        f"Aplicado no checkout. desconto={discount_cents}."
        + (f" order_id={order_id}." if order_id else "")
    )
    credit.notes = f"{credit.notes}\n{applied_note}".strip() if credit.notes else applied_note

    # Sessões com autoflush=False precisam de flush explícito para o próximo SELECT
    # na mesma transação enxergar status USED (evita reuso duplo no mesmo commit).
    db.flush()

    return CreditCheckoutApplication(
        requested=True,
        applied=True,
        reason="applied",
        credit_id=credit.id,
        discount_cents=discount_cents,
        final_amount_cents=final_amount_cents,
        currency=wallet_currency or order_currency,
    )


def restore_credit_after_failed_order_creation(
    *,
    db: Session,
    order_metadata: dict | None,
    now: datetime | None = None,
) -> bool:
    """
    Se o pedido for revertido após o crédito já ter sido marcado como USED no mesmo commit,
    reabre o crédito (ex.: falha do lifecycle após commit).
    """
    if not isinstance(order_metadata, Mapping):
        return False
    cap = dict(order_metadata).get("credit_application")
    if not isinstance(cap, dict) or not cap.get("applied") or not cap.get("credit_id"):
        return False

    ref = now or _utc_now()
    credit = (
        db.query(Credit)
        .filter(Credit.id == str(cap["credit_id"]))
        .with_for_update()
        .first()
    )
    if not credit or credit.status != CreditStatus.USED:
        return False

    credit.status = CreditStatus.AVAILABLE
    credit.used_at = None
    credit.updated_at = ref
    note = f"Crédito reaberto após compensação de pedido (lifecycle/order)."
    credit.notes = f"{credit.notes}\n{note}".strip() if credit.notes else note
    return True


def expire_overdue_available_credits(db: Session, *, now: datetime | None = None) -> int:
    ref = now or _utc_now()

    updated = (
        db.query(Credit)
        .filter(
            Credit.status == CreditStatus.AVAILABLE,
            Credit.expires_at <= ref,
            Credit.used_at.is_(None),
            Credit.revoked_at.is_(None),
        )
        .update(
            {
                "status": CreditStatus.EXPIRED,
                "updated_at": ref,
            },
            synchronize_session=False,
        )
    )
    return int(updated or 0)


def grant_expired_pickup_credit(
    *,
    db: Session,
    order: Order,
    ratio: float = 0.5,
    validity_days: int = EXPIRED_PICKUP_CREDIT_DAYS,
) -> CreditGrantResult:
    """
    Gera crédito de 50% para pedido expirado sem retirada.

    Regras:
    - 1 crédito por pedido (idempotência por credits.order_id unique)
    - validade de 30 dias
    - se já existir crédito do pedido, reaproveita
    - se não houver user_id, não cria crédito
    """
    if not order:
        return CreditGrantResult(
            created=False,
            credit_id=None,
            amount_cents=0,
            status=None,
            reason="order_missing",
            expires_at=None,
        )

    now = _utc_now()

    existing = get_credit_by_order_id(db, order_id=order.id)
    if existing:
        logger.info(
            "expired_pickup_credit_already_exists",
            extra={
                "order_id": order.id,
                "credit_id": existing.id,
                "credit_status": getattr(existing.status, "value", existing.status),
                "amount_cents": existing.amount_cents,
                "expires_at": existing.expires_at.isoformat() if existing.expires_at else None,
            },
        )
        return CreditGrantResult(
            created=False,
            credit_id=existing.id,
            amount_cents=int(existing.amount_cents or 0),
            status=getattr(existing.status, "value", existing.status),
            reason="already_exists",
            expires_at=existing.expires_at.isoformat() if existing.expires_at else None,
        )

    user_id = getattr(order, "user_id", None)
    if not user_id:
        logger.warning(
            "expired_pickup_credit_not_created_missing_user",
            extra={"order_id": order.id},
        )
        return CreditGrantResult(
            created=False,
            credit_id=None,
            amount_cents=0,
            status=None,
            reason="missing_user_id",
            expires_at=None,
        )

    amount_cents = _calculate_credit_amount_cents(order, ratio=ratio)
    if amount_cents <= 0:
        logger.warning(
            "expired_pickup_credit_not_created_invalid_amount",
            extra={
                "order_id": order.id,
                "order_amount_cents": getattr(order, "amount_cents", None),
                "calculated_credit_amount_cents": amount_cents,
            },
        )
        return CreditGrantResult(
            created=False,
            credit_id=None,
            amount_cents=0,
            status=None,
            reason="invalid_amount",
            expires_at=None,
        )

    expires_at = now + timedelta(days=validity_days)

    credit = Credit()
    credit.id = Credit.new_id()
    credit.user_id = user_id
    credit.order_id = order.id
    credit.amount_cents = amount_cents
    credit.status = CreditStatus.AVAILABLE
    credit.created_at = now
    credit.updated_at = now
    credit.expires_at = expires_at
    credit.used_at = None
    credit.revoked_at = None
    credit.source_type = "PICKUP_EXPIRATION"
    credit.source_reason = "pickup_not_redeemed_before_deadline"
    credit.notes = f"Crédito automático de {int(ratio * 100)}% por expiração de retirada."

    db.add(credit)
    db.flush()

    logger.info(
        "expired_pickup_credit_created",
        extra={
            "order_id": order.id,
            "credit_id": credit.id,
            "user_id": user_id,
            "amount_cents": amount_cents,
            "credit_status": CreditStatus.AVAILABLE.value,
            "expires_at": expires_at.isoformat(),
        },
    )

    return CreditGrantResult(
        created=True,
        credit_id=credit.id,
        amount_cents=amount_cents,
        status=CreditStatus.AVAILABLE.value,
        reason="created",
        expires_at=expires_at.isoformat(),
    )