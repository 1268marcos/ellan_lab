from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.ops_audit_service import record_ops_action_audit

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _to_iso_utc(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def run_inventory_reservations_expiry_once(db: Session) -> int:
    """
    Expira reservas ativas vencidas (expires_at <= now):
      - inventory_reservations: ACTIVE -> EXPIRED
      - product_inventory.quantity_reserved: decrementa pela quantidade da reserva
      - inventory_movements: registra movimento EXPIRED
      - ops_action_audit: registra INVENTORY_RESERVATION_EXPIRE
    """
    now = _utc_now()
    batch_size = int(settings.expiry_batch_size or 100)
    rows = db.execute(
        text(
            """
            SELECT
                id, order_id, product_id, locker_id, slot_size, quantity, expires_at
            FROM inventory_reservations
            WHERE status = 'ACTIVE'
              AND expires_at <= :now
            ORDER BY expires_at ASC, id ASC
            LIMIT :limit
            """
        ),
        {"now": now, "limit": batch_size},
    ).mappings().all()

    if not rows:
        return 0

    changed = 0
    for row in rows:
        reservation_id = str(row.get("id") or "")
        product_id = str(row.get("product_id") or "")
        locker_id = str(row.get("locker_id") or "")
        slot_size = str(row.get("slot_size") or "")
        quantity = int(row.get("quantity") or 0)
        if not reservation_id or not product_id or not locker_id or not slot_size or quantity <= 0:
            continue

        inventory_row = db.execute(
            text(
                """
                SELECT id, quantity_reserved
                FROM product_inventory
                WHERE product_id = :product_id
                  AND locker_id = :locker_id
                  AND slot_size = :slot_size
                """
            ),
            {"product_id": product_id, "locker_id": locker_id, "slot_size": slot_size},
        ).mappings().first()
        if not inventory_row:
            logger.warning(
                "inventory_expiry_inventory_not_found reservation_id=%s product_id=%s locker_id=%s slot_size=%s",
                reservation_id,
                product_id,
                locker_id,
                slot_size,
            )
            continue

        db.execute(
            text(
                """
                UPDATE product_inventory
                SET quantity_reserved = GREATEST(quantity_reserved - :quantity, 0),
                    updated_at = :updated_at
                WHERE id = :id
                """
            ),
            {"id": str(inventory_row.get("id")), "quantity": quantity, "updated_at": now},
        )
        db.execute(
            text(
                """
                UPDATE inventory_reservations
                SET status = 'EXPIRED',
                    updated_at = :updated_at
                WHERE id = :id
                """
            ),
            {"id": reservation_id, "updated_at": now},
        )
        movement_id = f"im_{reservation_id.replace('-', '')[:30]}"
        db.execute(
            text(
                """
                INSERT INTO inventory_movements (
                    id, product_id, locker_id, movement_type, quantity_delta,
                    reference_id, reference_type, note, occurred_at, created_by, created_at
                ) VALUES (
                    :id, :product_id, :locker_id, 'EXPIRED', 0,
                    :reference_id, 'ORDER', :note, :occurred_at, NULL, :created_at
                )
                """
            ),
            {
                "id": movement_id,
                "product_id": product_id,
                "locker_id": locker_id,
                "reference_id": str(row.get("order_id") or ""),
                "note": "Reserva expirada automaticamente por job.",
                "occurred_at": now,
                "created_at": now,
            },
        )
        try:
            record_ops_action_audit(
                db=db,
                action="INVENTORY_RESERVATION_EXPIRE",
                result="SUCCESS",
                correlation_id=f"inv-exp-{reservation_id}",
                user_id=None,
                role="ops_user",
                details={
                    "reservation_id": reservation_id,
                    "order_id": str(row.get("order_id") or ""),
                    "product_id": product_id,
                    "locker_id": locker_id,
                    "slot_size": slot_size,
                    "quantity": quantity,
                    "movement_id": movement_id,
                    "expires_at": _to_iso_utc(row.get("expires_at")),
                },
            )
        except Exception:
            logger.exception("inventory_expiry_audit_failed reservation_id=%s", reservation_id)

        changed += 1

    db.commit()
    logger.info("inventory_reservations_expiry_batch_changed=%s", changed)
    return changed

