# 01_source/order_pickup_service/app/services/credits_service.py
# 21/04/2026 - emissão de crédito 50% por expiração de pickup
# Observação:
# - usa o schema atual da tabela credits (sem expires_at / created_at)
# - idempotente por order_id unique
# - não inventa regra de expiração temporal enquanto o schema não suportar

from __future__ import annotations

import logging
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.credit import Credit, CreditStatus
from app.models.order import Order

logger = logging.getLogger(__name__)


@dataclass
class CreditGrantResult:
    created: bool
    credit_id: str | None
    amount_cents: int
    status: str | None
    reason: str


def _calculate_credit_amount_cents(order: Order, ratio: float = 0.5) -> int:
    amount_cents = int(getattr(order, "amount_cents", 0) or 0)
    if amount_cents <= 0:
        return 0

    granted = int(round(amount_cents * ratio))
    return max(granted, 0)


def get_credit_by_order_id(db: Session, *, order_id: str) -> Credit | None:
    return (
        db.query(Credit)
        .filter(Credit.order_id == order_id)
        .first()
    )


def grant_expired_pickup_credit(
    *,
    db: Session,
    order: Order,
    ratio: float = 0.5,
) -> CreditGrantResult:
    """
    Gera crédito de 50% para pedido expirado sem retirada.

    Regras atuais:
    - 1 crédito por pedido (idempotência por credits.order_id unique)
    - usa o schema atual minimalista
    - se não houver user_id, não cria crédito
    - se amount_cents inválido/zero, não cria crédito
    """
    if not order:
        return CreditGrantResult(
            created=False,
            credit_id=None,
            amount_cents=0,
            status=None,
            reason="order_missing",
        )

    existing = get_credit_by_order_id(db, order_id=order.id)
    if existing:
        logger.info(
            "expired_pickup_credit_already_exists",
            extra={
                "order_id": order.id,
                "credit_id": existing.id,
                "credit_status": getattr(existing.status, "value", existing.status),
                "amount_cents": existing.amount_cents,
            },
        )
        return CreditGrantResult(
            created=False,
            credit_id=existing.id,
            amount_cents=int(existing.amount_cents or 0),
            status=getattr(existing.status, "value", existing.status),
            reason="already_exists",
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
        )

    credit = Credit()
    credit.id = Credit.new_id()
    credit.user_id = user_id
    credit.order_id = order.id
    credit.amount_cents = amount_cents
    credit.status = CreditStatus.AVAILABLE

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
        },
    )

    return CreditGrantResult(
        created=True,
        credit_id=credit.id,
        amount_cents=amount_cents,
        status=CreditStatus.AVAILABLE.value,
        reason="created",
    )

