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


def _to_iso_utc(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def run_inventory_reserved_reconciliation_once(db: Session) -> dict:
    """
    Reconcilia divergências entre product_inventory.quantity_reserved e
    soma das reservas ACTIVE em inventory_reservations.
    """
    now = _utc_now()
    batch_size = int(getattr(settings, "inventory_reserved_reconciliation_batch_size", 100) or 100)
    limit = max(1, min(batch_size, 500))

    divergence_rows = db.execute(
        text(
            """
            SELECT
                pi.id AS inventory_id,
                pi.product_id,
                pi.locker_id,
                pi.slot_size,
                pi.quantity_reserved AS reserved_stored,
                COALESCE(ir.active_reserved, 0) AS reserved_active
            FROM product_inventory pi
            LEFT JOIN (
                SELECT
                    product_id,
                    locker_id,
                    slot_size,
                    SUM(quantity)::int AS active_reserved
                FROM inventory_reservations
                WHERE status = 'ACTIVE'
                GROUP BY product_id, locker_id, slot_size
            ) ir
              ON ir.product_id = pi.product_id
             AND ir.locker_id = pi.locker_id
             AND ir.slot_size = pi.slot_size
            WHERE pi.quantity_reserved <> COALESCE(ir.active_reserved, 0)
            ORDER BY ABS(pi.quantity_reserved - COALESCE(ir.active_reserved, 0)) DESC, pi.updated_at ASC
            LIMIT :limit
            """
        ),
        {"limit": limit},
    ).mappings().all()

    orphan_rows = db.execute(
        text(
            """
            SELECT
                ir.product_id,
                ir.locker_id,
                ir.slot_size,
                SUM(ir.quantity)::int AS reserved_active
            FROM inventory_reservations ir
            LEFT JOIN product_inventory pi
              ON pi.product_id = ir.product_id
             AND pi.locker_id = ir.locker_id
             AND pi.slot_size = ir.slot_size
            WHERE ir.status = 'ACTIVE'
              AND pi.id IS NULL
            GROUP BY ir.product_id, ir.locker_id, ir.slot_size
            ORDER BY SUM(ir.quantity) DESC
            LIMIT :limit
            """
        ),
        {"limit": limit},
    ).mappings().all()

    items: list[dict] = []
    auto_fixed = 0
    divergence_alerts = 0

    for row in divergence_rows:
        product_id = str(row.get("product_id") or "")
        locker_id = str(row.get("locker_id") or "")
        slot_size = str(row.get("slot_size") or "")
        reserved_stored = int(row.get("reserved_stored") or 0)
        reserved_active = int(row.get("reserved_active") or 0)
        delta = reserved_active - reserved_stored

        item = {
            "product_id": product_id,
            "locker_id": locker_id,
            "slot_size": slot_size,
            "reserved_stored": reserved_stored,
            "reserved_active": reserved_active,
            "delta": delta,
            "status": "AUTO_FIXED",
        }
        items.append(item)

        record_ops_action_audit(
            db=db,
            action="INVENTORY_RESERVED_DIVERGENCE_ALERT",
            result="ERROR",
            correlation_id=f"inv-reconcile-alert-{product_id}-{locker_id}-{slot_size}",
            user_id=None,
            role="system_worker",
            details={
                "source": "inventory_reserved_reconciliation_job",
                "product_id": product_id,
                "locker_id": locker_id,
                "slot_size": slot_size,
                "reserved_stored": reserved_stored,
                "reserved_active": reserved_active,
                "delta": delta,
                "checked_at": _to_iso_utc(now),
            },
        )
        divergence_alerts += 1

        db.execute(
            text(
                """
                UPDATE product_inventory
                SET quantity_reserved = :reserved_active,
                    updated_at = :updated_at
                WHERE id = :id
                """
            ),
            {
                "id": str(row.get("inventory_id") or ""),
                "reserved_active": reserved_active,
                "updated_at": now,
            },
        )

        record_ops_action_audit(
            db=db,
            action="INVENTORY_RESERVED_RECONCILE_AUTO_FIX",
            result="SUCCESS",
            correlation_id=f"inv-reconcile-fix-{product_id}-{locker_id}-{slot_size}",
            user_id=None,
            role="system_worker",
            details={
                "source": "inventory_reserved_reconciliation_job",
                "product_id": product_id,
                "locker_id": locker_id,
                "slot_size": slot_size,
                "before": {"quantity_reserved": reserved_stored},
                "after": {"quantity_reserved": reserved_active},
                "delta": delta,
                "checked_at": _to_iso_utc(now),
            },
        )
        auto_fixed += 1

    orphan_active_groups = 0
    for row in orphan_rows:
        orphan_item = {
            "product_id": str(row.get("product_id") or ""),
            "locker_id": str(row.get("locker_id") or ""),
            "slot_size": str(row.get("slot_size") or ""),
            "reserved_stored": 0,
            "reserved_active": int(row.get("reserved_active") or 0),
            "delta": int(row.get("reserved_active") or 0),
            "status": "ORPHAN_ACTIVE_RESERVATIONS",
        }
        items.append(orphan_item)
        record_ops_action_audit(
            db=db,
            action="INVENTORY_RESERVED_ORPHAN_ALERT",
            result="ERROR",
            correlation_id=(
                f"inv-reconcile-orphan-{orphan_item['product_id']}-{orphan_item['locker_id']}-{orphan_item['slot_size']}"
            ),
            user_id=None,
            role="system_worker",
            details={
                "source": "inventory_reserved_reconciliation_job",
                **orphan_item,
                "checked_at": _to_iso_utc(now),
            },
        )
        orphan_active_groups += 1
        divergence_alerts += 1

    db.commit()
    if auto_fixed or orphan_active_groups:
        logger.warning(
            "inventory_reserved_reconciliation auto_fixed=%s alerts=%s orphan_groups=%s",
            auto_fixed,
            divergence_alerts,
            orphan_active_groups,
        )

    return {
        "checked_at": _to_iso_utc(now),
        "auto_fixed": auto_fixed,
        "divergence_alerts": divergence_alerts,
        "orphan_active_groups": orphan_active_groups,
        "items": items,
    }

