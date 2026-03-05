"""
Job expiração ONLINE (janela 2h) + crédito 50% (opcional)

Regra:
- Se passou pickup_deadline_at e o pedido ainda está PAID_PENDING_PICKUP:
  - Order -> EXPIRED
  - Allocation -> RELEASED (ou outro estado existente no seu enum)
  - Locker slot -> OUT_OF_STOCK (cinza, aguardando reposição) [efeito externo]
  - locker_release(allocation_id) [efeito externo]
  - Crédito 50% (se model existir) [efeito interno]

Notas de compatibilidade:
- SQLite: não usamos with_for_update(skip_locked=True)
- AllocationState.EXPIRED não existe no seu enum atual -> usamos RELEASED
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from app.models.order import Order, OrderChannel, OrderStatus
from app.models.allocation import Allocation, AllocationState
from app.services import backend_client

logger = logging.getLogger(__name__)

BATCH_SIZE = int(os.getenv("EXPIRY_BATCH_SIZE", "100"))
MAX_RETRIES = int(os.getenv("EXPIRY_MAX_RETRIES", "3"))

# habilitar/desabilitar crédito sem travar build
ENABLE_CREDIT = os.getenv("EXPIRY_ENABLE_CREDIT", "false").lower() == "true"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _try_import_credit():
    """
    Import opcional para não quebrar o serviço se o model ainda não existe.
    """
    try:
        from app.models.credit import Credit, CreditStatus  # type: ignore
        return Credit, CreditStatus
    except Exception:
        return None, None


def run_expiry_once(db: Session) -> int:
    """
    Processa 1 batch de pedidos ONLINE expirados.
    Retorna quantos pedidos foram marcados EXPIRED (efeitos externos são best-effort).
    """
    now = _utc_now()
    changed = 0

    # 1) busca candidatos (SQLite-friendly)
    expired_orders = (
        db.query(Order)
        .filter(
            Order.channel == OrderChannel.ONLINE,
            Order.status == OrderStatus.PAID_PENDING_PICKUP,
            Order.pickup_deadline_at.isnot(None),
            Order.pickup_deadline_at <= now.replace(tzinfo=None),
        )
        .limit(BATCH_SIZE)
        .all()
    )

    if not expired_orders:
        return 0

    logger.info(f"[expiry] encontrados {len(expired_orders)} pedidos (batch={BATCH_SIZE})")

    # Processa pedido a pedido para transação curta
    processed: list[Tuple[str, Optional[str], Optional[int], str]] = []
    # (order_id, allocation_id, slot, region)

    for order in expired_orders:
        try:
            result = _process_expired_order(db, order)
            if result:
                changed += 1
                processed.append(result)
                db.commit()
            else:
                db.rollback()
        except Exception as e:
            db.rollback()
            logger.error(f"[expiry] erro ao processar order={order.id}: {e}", exc_info=True)
            continue

    # Efeitos externos (fora da transação)
    for order_id, allocation_id, slot, region in processed:
        try:
            _process_external_effects(order_id=order_id, allocation_id=allocation_id, slot=slot, region=region)
        except Exception as e:
            logger.error(f"[expiry] erro efeitos externos order={order_id}: {e}", exc_info=True)

    logger.info(f"[expiry] batch finalizado: {changed}/{len(expired_orders)}")
    return changed


def _process_expired_order(db: Session, order: Order) -> Optional[Tuple[str, Optional[str], Optional[int], str]]:
    """
    Marca order/alloc internamente como expirados. Não chama backend aqui.
    Retorna dados necessários para efeitos externos.
    """
    if order.status != OrderStatus.PAID_PENDING_PICKUP:
        return None

    region = getattr(order, "region", None) or "PT"

    allocation = db.query(Allocation).filter(Allocation.order_id == order.id).first()

    # (opcional) crédito 50% se existir model e user_id
    if ENABLE_CREDIT:
        Credit, CreditStatus = _try_import_credit()
        if Credit and CreditStatus and getattr(order, "user_id", None) and getattr(order, "amount_cents", None):
            try:
                existing = db.query(Credit).filter(Credit.order_id == order.id).first()
                if not existing:
                    credit_amount = int(int(order.amount_cents) * 0.50)
                    credit = Credit(
                        id=Credit.new_id(),  # se existir
                        user_id=order.user_id,
                        order_id=order.id,
                        amount_cents=credit_amount,
                        status=CreditStatus.AVAILABLE,
                    )
                    db.add(credit)
                    logger.info(f"[expiry] crédito {credit_amount} cents criado order={order.id}")
            except Exception as e:
                # não derruba expiração por causa de crédito
                logger.warning(f"[expiry] falha ao criar crédito order={order.id}: {e}")

    # 1) atualiza estados internos
    order.status = OrderStatus.EXPIRED

    alloc_id = None
    slot = None

    if allocation:
        alloc_id = allocation.id
        slot = allocation.slot

        # ✅ NÃO existe AllocationState.EXPIRED -> poderiamos usar RELEASED (ou outro que exista)
        # Se você tiver outro estado melhor (ex.: CANCELLED/EXPIRED), trocamos depois. [foi trocado para EXPIRED]
        allocation.state = AllocationState.EXPIRED
        allocation.locked_until = None

    logger.info(f"[expiry] order={order.id} marcado EXPIRED; alloc={alloc_id} slot={slot}")
    return (order.id, alloc_id, slot, region)


def _process_external_effects(*, order_id: str, allocation_id: Optional[str], slot: Optional[int], region: str) -> None:
    """
    Efeitos no backend do totem. Best-effort com retries.
    """
    if slot is not None:
        for attempt in range(MAX_RETRIES):
            try:
                backend_client.locker_set_state(region, int(slot), "OUT_OF_STOCK")
                break
            except Exception as e:
                if attempt == MAX_RETRIES - 1:
                    logger.error(f"[expiry] set_state falhou order={order_id} slot={slot}: {e}")
                else:
                    logger.warning(f"[expiry] set_state retry {attempt+1} order={order_id}: {e}")

    if allocation_id:
        for attempt in range(MAX_RETRIES):
            try:
                backend_client.locker_release(region, allocation_id)
                break
            except Exception as e:
                if attempt == MAX_RETRIES - 1:
                    logger.error(f"[expiry] locker_release falhou order={order_id} alloc={allocation_id}: {e}")
                else:
                    logger.warning(f"[expiry] locker_release retry {attempt+1} order={order_id}: {e}")


def run_expiry(db: Session) -> int:
    """
    Execução simplificada (1 batch).
    """
    return run_expiry_once(db)