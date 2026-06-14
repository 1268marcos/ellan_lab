# app/services/wallet_credits.py (ex-credits_domain / wallet_credits_bridge)
# 21/04/2026 - emissão e expiração de crédito 50% por pickup expirado

from __future__ import annotations

import logging
from collections import defaultdict
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
PICKUP_EXPIRATION_SOURCE_TYPE = "PICKUP_EXPIRATION"
DEFAULT_CREDIT_CURRENCY = "BRL"


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


def normalize_currency_code(value: str | None) -> str:
    code = str(value or "").strip().upper()
    return code or DEFAULT_CREDIT_CURRENCY


def credit_currency_from_metadata(credit: Credit) -> str | None:
    meta = getattr(credit, "metadata_json", None)
    if not isinstance(meta, Mapping):
        return None
    raw = meta.get("currency")
    if raw is None:
        return None
    code = str(raw).strip().upper()
    return code or None


def load_order_currencies_by_id(db: Session, order_ids: list[str]) -> dict[str, str]:
    ids = list(dict.fromkeys(str(oid).strip() for oid in order_ids if oid))
    if not ids:
        return {}

    try:
        rows = db.query(Order.id, Order.currency).filter(Order.id.in_(ids)).all()
    except SQLAlchemyError as exc:
        logger.warning(
            "load_order_currencies_by_id_failed",
            extra={"error_type": exc.__class__.__name__, "count": len(ids)},
        )
        return {}

    out: dict[str, str] = {}
    for order_id, currency in rows:
        oid = str(order_id or "").strip()
        if not oid:
            continue
        out[oid] = normalize_currency_code(currency)
    return out


def resolve_credit_currency(
    credit: Credit,
    *,
    order_currency: str | None = None,
    wallet_currency: str | None = None,
) -> str:
    """
    Moeda canónica do crédito (ordem de precedência):
    metadata_json.currency → moeda do pedido de origem → carteira → BRL.
    """
    from_meta = credit_currency_from_metadata(credit)
    if from_meta:
        return from_meta
    if order_currency:
        return normalize_currency_code(order_currency)
    if wallet_currency:
        return normalize_currency_code(wallet_currency)
    return DEFAULT_CREDIT_CURRENCY


@dataclass
class CreditsCurrencySummary:
    balances_by_currency: dict[str, int]
    available_by_currency: dict[str, int]
    display_currency: str
    display_available_balance_cents: int
    display_available_count: int
    display_expiring_soon_count: int


def summarize_credits_by_currency(
    credits: list[Credit],
    *,
    order_currencies: Mapping[str, str],
    wallet_currency: str | None,
    now: datetime,
    expiring_soon_seconds: int = 7 * 24 * 60 * 60,
) -> CreditsCurrencySummary:
    wallet_norm = normalize_currency_code(wallet_currency) if wallet_currency else None
    display_currency = wallet_norm or DEFAULT_CREDIT_CURRENCY

    balances_by_currency: dict[str, int] = defaultdict(int)
    available_by_currency: dict[str, int] = defaultdict(int)
    display_available_balance_cents = 0
    display_available_count = 0
    display_expiring_soon_count = 0

    for credit in credits:
        currency = resolve_credit_currency(
            credit,
            order_currency=order_currencies.get(credit.order_id or ""),
            wallet_currency=wallet_currency,
        )
        remaining = int(credit.amount_cents or 0)
        balances_by_currency[currency] += remaining

        if not credit.is_available_now(now=now):
            continue

        available_by_currency[currency] += remaining
        if currency != display_currency:
            continue

        display_available_balance_cents += remaining
        display_available_count += 1

        expires_at = credit.expires_at
        if expires_at is not None:
            expires_at_utc = (
                expires_at if expires_at.tzinfo else expires_at.replace(tzinfo=timezone.utc)
            )
            delta = expires_at_utc - now
            if 0 <= delta.total_seconds() <= expiring_soon_seconds:
                display_expiring_soon_count += 1

    if not wallet_norm and available_by_currency:
        display_currency = max(available_by_currency.items(), key=lambda item: item[1])[0]
        display_available_balance_cents = available_by_currency[display_currency]
        display_available_count = sum(
            1 for c in credits if c.is_available_now(now=now)
            and resolve_credit_currency(
                c,
                order_currency=order_currencies.get(c.order_id or ""),
                wallet_currency=wallet_currency,
            )
            == display_currency
        )
        display_expiring_soon_count = 0
        for credit in credits:
            if not credit.is_available_now(now=now):
                continue
            currency = resolve_credit_currency(
                credit,
                order_currency=order_currencies.get(credit.order_id or ""),
                wallet_currency=wallet_currency,
            )
            if currency != display_currency:
                continue
            expires_at = credit.expires_at
            if expires_at is None:
                continue
            expires_at_utc = (
                expires_at if expires_at.tzinfo else expires_at.replace(tzinfo=timezone.utc)
            )
            delta = expires_at_utc - now
            if 0 <= delta.total_seconds() <= expiring_soon_seconds:
                display_expiring_soon_count += 1

    return CreditsCurrencySummary(
        balances_by_currency=dict(sorted(balances_by_currency.items())),
        available_by_currency=dict(sorted(available_by_currency.items())),
        display_currency=display_currency,
        display_available_balance_cents=display_available_balance_cents,
        display_available_count=display_available_count,
        display_expiring_soon_count=display_expiring_soon_count,
    )


def _calculate_credit_amount_cents(order: Order, ratio: float = 0.5) -> int:
    amount_cents = int(getattr(order, "amount_cents", 0) or 0)
    if amount_cents <= 0:
        return 0
    granted = int(round(amount_cents * ratio))
    return max(granted, 0)


def get_credit_by_order_id(db: Session, *, order_id: str) -> Credit | None:
    return (
        db.query(Credit)
        .filter(
            Credit.order_id == order_id,
            Credit.source_type == PICKUP_EXPIRATION_SOURCE_TYPE,
            Credit.deleted_at.is_(None),
        )
        .first()
    )


def get_user_wallet_id(db: Session, *, user_id: str | None) -> str | None:
    if not user_id:
        return None

    try:
        return db.execute(
            text(
                """
                SELECT id
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
            "get_user_wallet_id_failed",
            extra={"user_id": user_id, "error_type": exc.__class__.__name__},
        )
        return None


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
    order_currency: str | None = None,
    wallet_currency: str | None = None,
    requested_credit_id: str | None = None,
    now: datetime | None = None,
    lock_for_update: bool = True,
) -> Credit | None:
    """
    Seleciona um crédito elegível para desconto no checkout.

    Critérios (todos obrigatórios):
    - ``user_id`` do titular;
    - ``status == AVAILABLE``, não expirado, sem ``used_at`` / ``revoked_at``;
    - ``amount_cents <= order_amount_cents - 1`` (pedido permanece com valor mínimo de 1);
    - moeda do crédito igual à ``order_currency`` quando informada.

    Ordenação: menor ``expires_at`` primeiro, depois ``created_at`` (FIFO dentro da
    mesma validade).

    Locking (padrão ``lock_for_update=True``):
    Emite ``SELECT ... FOR UPDATE SKIP LOCKED`` via ``Query.with_for_update(skip_locked=True)``.
    A linha retornada fica bloqueada até o fim da transação; linhas já locked por outro
    checkout são ignoradas (sem fila de espera). Preview somente-leitura deve passar
    ``lock_for_update=False``.
    """
    if not user_id:
        return None

    max_discount_cents = int(order_amount_cents or 0) - 1
    if max_discount_cents <= 0:
        return None

    ref = now or _utc_now()
    target_currency = normalize_currency_code(order_currency) if order_currency else None

    query = (
        db.query(Credit)
        .filter(
            Credit.user_id == user_id,
            Credit.status == CreditStatus.AVAILABLE,
            Credit.deleted_at.is_(None),
            Credit.expires_at > ref,
            Credit.used_at.is_(None),
            Credit.revoked_at.is_(None),
            Credit.remaining > 0,
            Credit.amount_cents <= max_discount_cents,
        )
        .order_by(Credit.expires_at.asc(), Credit.created_at.asc())
    )

    if requested_credit_id:
        query = query.filter(Credit.id == requested_credit_id)

    if lock_for_update:
        query = query.with_for_update(skip_locked=True)

    candidates = query.all()
    if not candidates:
        return None

    order_ids = [c.order_id for c in candidates if c.order_id]
    order_currencies = load_order_currencies_by_id(db, order_ids)

    for credit in candidates:
        credit_currency = resolve_credit_currency(
            credit,
            order_currency=order_currencies.get(credit.order_id or ""),
            wallet_currency=wallet_currency,
        )
        if target_currency and credit_currency != target_currency:
            continue
        return credit

    return None


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
    # Estratégia de locking no checkout (mesma transação que cria o pedido):
    # 1) SELECT ... FOR UPDATE SKIP LOCKED — reserva a linha do crédito sem bloquear
    #    checkouts concorrentes em fila; quem perde o lock recebe None.
    # 2) UPDATE ORM (status USED + flush) — visível para o próximo SELECT na sessão.
    # 3) commit do caller — libera o lock; outras transações não reutilizam o crédito.
    credit = select_checkout_credit_candidate(
        db=db,
        user_id=user_id,
        order_amount_cents=base_amount,
        order_currency=order_currency,
        wallet_currency=wallet_currency,
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

    order_currencies = load_order_currencies_by_id(db, [credit.order_id] if credit.order_id else [])
    applied_currency = resolve_credit_currency(
        credit,
        order_currency=order_currencies.get(credit.order_id or ""),
        wallet_currency=wallet_currency,
    )

    credit.status = CreditStatus.USED
    credit.used_at = ref
    credit.updated_at = ref
    credit.remaining = 0
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
        currency=applied_currency or order_currency,
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
    credit.remaining = int(credit.amount or 0)
    note = f"Crédito reaberto após compensação de pedido (lifecycle/order)."
    credit.notes = f"{credit.notes}\n{note}".strip() if credit.notes else note
    return True


def expire_overdue_available_credits(db: Session, *, now: datetime | None = None) -> int:
    ref = now or _utc_now()

    updated = (
        db.query(Credit)
        .filter(
            Credit.status == CreditStatus.AVAILABLE,
            Credit.deleted_at.is_(None),
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
    wallet_id = get_user_wallet_id(db, user_id=user_id)
    order_currency = normalize_currency_code(getattr(order, "currency", None))
    wallet_currency = get_user_wallet_currency(db, user_id=user_id)
    credit_currency = order_currency
    if wallet_currency and normalize_currency_code(wallet_currency) == order_currency:
        credit_currency = normalize_currency_code(wallet_currency)

    credit = Credit()
    credit.id = Credit.new_id()
    credit.user_id = user_id
    credit.order_id = order.id
    credit.wallet_id = wallet_id
    credit.amount_cents = amount_cents
    credit.promotional = True
    credit.status = CreditStatus.AVAILABLE
    credit.created_at = now
    credit.updated_at = now
    credit.expires_at = expires_at
    credit.used_at = None
    credit.revoked_at = None
    credit.source_type = PICKUP_EXPIRATION_SOURCE_TYPE
    credit.source_reason = "pickup_not_redeemed_before_deadline"
    credit.notes = f"Crédito automático de {int(ratio * 100)}% por expiração de retirada."
    credit.metadata_json = {
        "type": PICKUP_EXPIRATION_SOURCE_TYPE,
        "currency": credit_currency,
        "order_amount_cents": int(getattr(order, "amount_cents", 0) or 0),
        "credit_ratio": ratio,
    }

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
