# Race condition: 10 checkouts simultâneos disputando o mesmo crédito.
#
# Requer Postgres (ORDER_PICKUP_TEST_DATABASE_URL) — FOR UPDATE SKIP LOCKED
# não reproduz concorrência real em SQLite.

from __future__ import annotations

import asyncio
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.db import Base
from app.models.credit import Credit, CreditStatus
from app.services.wallet_credits import apply_credit_for_checkout

CONCURRENT_REQUESTS = 10
BASE_AMOUNT_CENTS = 2000
CREDIT_DISCOUNT_CENTS = 500


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class OrderCreditAttemptResult:
    """Resultado de uma tentativa de criar pedido (etapa de crédito do checkout)."""

    order_id: str
    applied: bool
    discount_cents: int
    final_amount_cents: int
    reason: str
    error: str | None = None


def _insert_available_credit(session, *, credit_id: str, user_id: str, amount_cents: int) -> None:
    now = _utc_now()
    session.add(
        Credit(
            id=credit_id,
            user_id=user_id,
            order_id=f"orig-{credit_id}",
            amount_cents=amount_cents,
            status=CreditStatus.AVAILABLE,
            created_at=now,
            updated_at=now,
            expires_at=now + timedelta(days=30),
            used_at=None,
            revoked_at=None,
        )
    )
    session.commit()


def _attempt_create_order_with_credit(
    Session,
    *,
    user_id: str,
    credit_id: str,
    order_id: str,
    base_amount_cents: int,
) -> OrderCreditAttemptResult:
    """
    Simula a etapa de crédito de ``create_order_core`` (apply + commit por pedido).
    """
    db = Session()
    try:
        credit_application = apply_credit_for_checkout(
            db=db,
            user_id=user_id,
            base_amount_cents=base_amount_cents,
            order_currency="BRL",
            order_id=order_id,
            use_credit=True,
            requested_credit_id=credit_id,
        )
        db.commit()
        return OrderCreditAttemptResult(
            order_id=order_id,
            applied=bool(credit_application.applied),
            discount_cents=int(credit_application.discount_cents or 0),
            final_amount_cents=int(credit_application.final_amount_cents),
            reason=str(credit_application.reason or ""),
        )
    except Exception as exc:  # noqa: BLE001 — harness de concorrência
        db.rollback()
        return OrderCreditAttemptResult(
            order_id=order_id,
            applied=False,
            discount_cents=0,
            final_amount_cents=base_amount_cents,
            reason="error",
            error=str(exc),
        )
    finally:
        db.close()


async def _run_concurrent_order_credit_attempts(
    Session,
    *,
    user_id: str,
    credit_id: str,
    run_id: str,
    n: int = CONCURRENT_REQUESTS,
) -> list[OrderCreditAttemptResult]:
    async def _one(index: int) -> OrderCreditAttemptResult:
        order_id = f"order-race-{run_id}-{index}"
        return await asyncio.to_thread(
            _attempt_create_order_with_credit,
            Session,
            user_id=user_id,
            credit_id=credit_id,
            order_id=order_id,
            base_amount_cents=BASE_AMOUNT_CENTS,
        )

    return list(await asyncio.gather(*[_one(i) for i in range(n)]))


def _assert_no_double_credit_use(
    *,
    results: list[OrderCreditAttemptResult],
    credit_row: Credit,
) -> None:
    applied_results = [r for r in results if r.applied]
    with_discount = [r for r in results if r.discount_cents > 0]
    without_discount = [r for r in results if r.discount_cents == 0]

    assert len(applied_results) == 1, (
        f"Esperado 1 pedido com crédito aplicado; obtido {len(applied_results)}: "
        f"{[(r.order_id, r.discount_cents, r.reason) for r in applied_results]}"
    )
    assert len(with_discount) == 1, (
        f"Esperado 1 pedido com desconto; obtido {len(with_discount)}"
    )
    assert len(without_discount) == CONCURRENT_REQUESTS - 1, (
        f"Esperado {CONCURRENT_REQUESTS - 1} pedidos com discount_cents=0; "
        f"obtido {len(without_discount)}"
    )

    for r in without_discount:
        assert r.discount_cents == 0
        assert r.final_amount_cents == BASE_AMOUNT_CENTS

    winner = applied_results[0]
    assert winner.discount_cents == CREDIT_DISCOUNT_CENTS
    assert winner.final_amount_cents == BASE_AMOUNT_CENTS - CREDIT_DISCOUNT_CENTS

    assert credit_row.status == CreditStatus.USED
    assert credit_row.used_at is not None

    # Nenhum crédito foi "consumido" duas vezes: só uma vitória com desconto > 0.
    assert sum(1 for r in results if r.applied and r.discount_cents > 0) == 1


@pytest.mark.skipif(
    not os.getenv("ORDER_PICKUP_TEST_DATABASE_URL"),
    reason="Defina ORDER_PICKUP_TEST_DATABASE_URL (Postgres) para race condition real.",
)
def test_concurrent_order_create_same_credit_no_double_use():
    """
    10 requisições simultâneas (asyncio.gather) disputam o mesmo crédito no checkout.

    Verifica:
    1. O crédito fica USED uma única vez (sem reuso duplo).
    2. Apenas um pedido recebe desconto.
    3. Os demais pedidos têm discount_cents = 0.
    """
    url = os.environ["ORDER_PICKUP_TEST_DATABASE_URL"]
    eng = create_engine(url, future=True)
    run_id = uuid.uuid4().hex[:12]
    credit_id = f"credit-race-{run_id}"
    user_id = f"user-race-{run_id}"

    Session = sessionmaker(bind=eng, autoflush=False, autocommit=False, future=True)
    try:
        Base.metadata.create_all(bind=eng, tables=[Credit.__table__])
        seed = Session()
        try:
            _insert_available_credit(
                seed,
                credit_id=credit_id,
                user_id=user_id,
                amount_cents=CREDIT_DISCOUNT_CENTS,
            )
        finally:
            seed.close()

        results = asyncio.run(
            _run_concurrent_order_credit_attempts(
                Session,
                user_id=user_id,
                credit_id=credit_id,
                run_id=run_id,
            )
        )

        errors = [r for r in results if r.error]
        assert not errors, f"workers raised: {errors}"

        verify = Session()
        try:
            credit_row = verify.query(Credit).filter(Credit.id == credit_id).one()
            _assert_no_double_credit_use(results=results, credit_row=credit_row)
        finally:
            verify.close()
    finally:
        cleanup = Session()
        try:
            cleanup.query(Credit).filter(Credit.id == credit_id).delete(synchronize_session=False)
            cleanup.commit()
        finally:
            cleanup.close()
        eng.dispose()
