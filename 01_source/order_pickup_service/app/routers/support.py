from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.allocation import Allocation
from app.models.ops_action_audit import OpsActionAudit
from app.models.order import Order
from app.models.pickup import Pickup
from app.services.fiscal_resolve import resolve_fiscal_for_order
from app.services.ops_audit_service import record_ops_action_audit

router = APIRouter(prefix="/api/v1/support", tags=["Suporte"])


class EscalateRequest(BaseModel):
    reason: str | None = None
    escalated_to: str = "N2"


def _enum_value(value: Any) -> str | None:
    if value is None:
        return None
    return str(getattr(value, "value", value))


def _dt_iso(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    return str(value)


def _event(
    *,
    kind: str,
    event: str,
    status: str | None,
    timestamp: Any,
    source: str,
    detail: dict[str, Any],
) -> dict[str, Any]:
    return {
        "kind": kind,
        "event": event,
        "status": status,
        "timestamp": _dt_iso(timestamp),
        "source": source,
        "detail": detail,
    }


def _table_exists(db: Session, table_name: str) -> bool:
    try:
        return table_name in set(inspect(db.get_bind()).get_table_names())
    except SQLAlchemyError:
        db.rollback()
        return False


def _order_events(order: Order) -> list[dict[str, Any]]:
    events = [
        _event(
            kind="order",
            event="order.created",
            status=_enum_value(order.status),
            timestamp=getattr(order, "created_at", None),
            source="order_pickup_service.orders",
            detail={
                "order_id": order.id,
                "channel": _enum_value(getattr(order, "channel", None)),
                "region": getattr(order, "region", None),
                "totem_id": getattr(order, "totem_id", None),
                "sku_id": getattr(order, "sku_id", None),
                "amount_cents": getattr(order, "amount_cents", None),
                "currency": getattr(order, "currency", None),
            },
        )
    ]

    dated_order_events = [
        ("payment.updated", getattr(order, "payment_status", None), getattr(order, "payment_updated_at", None)),
        ("order.paid", getattr(order, "payment_status", None), getattr(order, "paid_at", None)),
        ("order.picked_up", getattr(order, "status", None), getattr(order, "picked_up_at", None)),
        ("order.cancelled", getattr(order, "status", None), getattr(order, "cancelled_at", None)),
        ("order.refunded", getattr(order, "payment_status", None), getattr(order, "refunded_at", None)),
        ("order.updated", getattr(order, "status", None), getattr(order, "updated_at", None)),
    ]

    for event_name, status, timestamp in dated_order_events:
        if timestamp is None:
            continue
        events.append(
            _event(
                kind="order",
                event=event_name,
                status=_enum_value(status),
                timestamp=timestamp,
                source="order_pickup_service.orders",
                detail={"order_id": order.id},
            )
        )

    return events


def _allocation_event(allocation: Allocation | None) -> dict[str, Any] | None:
    if allocation is None:
        return None
    return _event(
        kind="allocation",
        event="allocation.state",
        status=_enum_value(allocation.state),
        timestamp=getattr(allocation, "updated_at", None) or getattr(allocation, "created_at", None),
        source="order_pickup_service.allocations",
        detail={
            "allocation_id": allocation.id,
            "locker_id": allocation.locker_id,
            "slot": allocation.slot,
            "locked_until": _dt_iso(getattr(allocation, "locked_until", None)),
        },
    )


def _pickup_event(pickup: Pickup | None) -> dict[str, Any] | None:
    if pickup is None:
        return None
    return _event(
        kind="pickup",
        event="pickup.state",
        status=_enum_value(pickup.status),
        timestamp=getattr(pickup, "updated_at", None) or getattr(pickup, "created_at", None),
        source="order_pickup_service.pickups",
        detail={
            "pickup_id": pickup.id,
            "lifecycle_stage": _enum_value(pickup.lifecycle_stage),
            "locker_id": pickup.locker_id,
            "machine_id": pickup.machine_id,
            "slot": pickup.slot,
            "expires_at": _dt_iso(pickup.expires_at),
        },
    )


def _latest_escalation(db: Session, order_id: str) -> OpsActionAudit | None:
    if not _table_exists(db, "ops_action_audit"):
        return None
    return (
        db.query(OpsActionAudit)
        .filter(
            OpsActionAudit.order_id == order_id,
            OpsActionAudit.action == "SUPPORT_ESCALATE",
            OpsActionAudit.result == "SUCCESS",
        )
        .order_by(OpsActionAudit.created_at.desc(), OpsActionAudit.id.desc())
        .first()
    )


def _escalation_event(escalation: OpsActionAudit | None) -> dict[str, Any] | None:
    if escalation is None:
        return None
    details = escalation.details_json or {}
    return _event(
        kind="support",
        event="support.escalated",
        status="escalated",
        timestamp=escalation.created_at,
        source="order_pickup_service.ops_action_audit",
        detail={
            "audit_id": escalation.id,
            "order_id": escalation.order_id,
            "escalated_to": details.get("escalated_to") or "N2",
            "reason": details.get("reason"),
            "correlation_id": escalation.correlation_id,
        },
    )


def _lifecycle_events(db: Session, order_id: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not _table_exists(db, "domain_events"):
        return [], {"status": "missing_table", "source": "order_lifecycle_service.domain_events"}

    dialect = db.get_bind().dialect.name
    if dialect == "postgresql":
        query = text(
            """
            SELECT event_key, aggregate_type, aggregate_id, event_name, status,
                   payload, occurred_at, created_at
            FROM domain_events
            WHERE aggregate_id = :order_id
               OR payload ->> 'order_id' = :order_id
            ORDER BY occurred_at ASC, created_at ASC
            LIMIT 100
            """
        )
    else:
        query = text(
            """
            SELECT event_key, aggregate_type, aggregate_id, event_name, status,
                   payload, occurred_at, created_at
            FROM domain_events
            WHERE aggregate_id = :order_id
               OR json_extract(payload, '$.order_id') = :order_id
            ORDER BY occurred_at ASC, created_at ASC
            LIMIT 100
            """
        )

    try:
        rows = db.execute(query, {"order_id": order_id}).mappings().all()
    except SQLAlchemyError as exc:
        db.rollback()
        return [], {
            "status": "error",
            "source": "order_lifecycle_service.domain_events",
            "error_type": exc.__class__.__name__,
        }

    events: list[dict[str, Any]] = []
    for row in rows:
        payload = row.get("payload")
        detail = payload if isinstance(payload, dict) else {"payload": payload}
        events.append(
            _event(
                kind="lifecycle",
                event=str(row.get("event_name") or "lifecycle.event"),
                status=str(row.get("status") or ""),
                timestamp=row.get("occurred_at") or row.get("created_at"),
                source="order_lifecycle_service.domain_events",
                detail={
                    "event_key": row.get("event_key"),
                    "aggregate_type": row.get("aggregate_type"),
                    "aggregate_id": row.get("aggregate_id"),
                    "payload": detail,
                },
            )
        )

    return events, {
        "status": "ok",
        "source": "order_lifecycle_service.domain_events",
        "count": len(events),
    }


def _fiscal_invoice_event(db: Session, order_id: str) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    fiscal = resolve_fiscal_for_order(db, order_id)
    if fiscal is None:
        return None, {
            "status": "not_found",
            "source": "billing_fiscal_service.invoices",
        }

    source = "billing_fiscal_service.invoices"
    if fiscal.__class__.__name__ == "FiscalDocument":
        source = "order_pickup_service.fiscal_documents"

    return (
        _event(
            kind="invoice",
            event="invoice.issued" if getattr(fiscal, "issued_at", None) else "invoice.current",
            status=getattr(fiscal, "send_status", None) or getattr(fiscal, "print_status", None),
            timestamp=getattr(fiscal, "issued_at", None) or getattr(fiscal, "created_at", None),
            source=source,
            detail={
                "invoice_id": getattr(fiscal, "id", None),
                "receipt_code": getattr(fiscal, "receipt_code", None),
                "document_type": getattr(fiscal, "document_type", None),
                "amount_cents": getattr(fiscal, "amount_cents", None),
                "currency": getattr(fiscal, "currency", None),
                "attempt": getattr(fiscal, "attempt", None),
            },
        ),
        {
            "status": "ok",
            "source": source,
            "invoice_id": getattr(fiscal, "id", None),
        },
    )


def _derive_next_action(
    *,
    order: Order,
    allocation: Allocation | None,
    pickup: Pickup | None,
    invoice_source: dict[str, Any],
    lifecycle_source: dict[str, Any],
) -> str:
    if pickup and _enum_value(pickup.status) == "ACTIVE":
        return "guide_customer_to_pickup"
    if invoice_source.get("status") == "not_found" and _enum_value(order.payment_status) == "APPROVED":
        return "request_invoice_issue"
    if allocation and _enum_value(allocation.state) in {"ERROR", "MAINTENANCE"}:
        return "escalate_to_n2"
    if lifecycle_source.get("status") == "error":
        return "check_lifecycle_events"
    return "review_order_state"


@router.get("/order/{order_id}")
def get_order_timeline(order_id: str, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if order is None:
        raise HTTPException(
            status_code=404,
            detail={
                "type": "ORDER_NOT_FOUND",
                "message": "Order not found for support timeline.",
                "order_id": order_id,
            },
        )

    allocation = db.query(Allocation).filter(Allocation.order_id == order_id).first()
    pickup = db.query(Pickup).filter(Pickup.order_id == order_id).first()
    escalation = _latest_escalation(db, order_id)

    timeline = _order_events(order)

    allocation_event = _allocation_event(allocation)
    if allocation_event is not None:
        timeline.append(allocation_event)

    pickup_event = _pickup_event(pickup)
    if pickup_event is not None:
        timeline.append(pickup_event)

    escalation_event = _escalation_event(escalation)
    if escalation_event is not None:
        timeline.append(escalation_event)

    lifecycle_events, lifecycle_source = _lifecycle_events(db, order_id)
    timeline.extend(lifecycle_events)

    invoice_event, invoice_source = _fiscal_invoice_event(db, order_id)
    if invoice_event is not None:
        timeline.append(invoice_event)

    timeline.sort(key=lambda item: item.get("timestamp") or "")

    next_action = _derive_next_action(
        order=order,
        allocation=allocation,
        pickup=pickup,
        invoice_source=invoice_source,
        lifecycle_source=lifecycle_source,
    )
    escalated_to = None
    if escalation is not None:
        escalated_to = (escalation.details_json or {}).get("escalated_to") or "N2"

    return {
        "order_id": order_id,
        "status": _enum_value(order.status),
        "next_action": next_action,
        "escalated_to": escalated_to,
        "summary": {
            "order_status": _enum_value(order.status),
            "payment_status": _enum_value(order.payment_status),
            "allocation_state": _enum_value(allocation.state) if allocation else None,
            "pickup_status": _enum_value(pickup.status) if pickup else None,
            "invoice_status": invoice_source.get("status"),
            "escalated_to": escalated_to,
            "next_action": next_action,
        },
        "sources": {
            "order": {"status": "ok", "source": "order_pickup_service.orders"},
            "lifecycle": lifecycle_source,
            "invoice": invoice_source,
        },
        "timeline": timeline,
        "events": timeline,
    }


@router.post("/order/{order_id}/escalate")
def escalate_to_n2(
    order_id: str,
    payload: EscalateRequest | None = None,
    reason: str | None = None,
    db: Session = Depends(get_db),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if order is None:
        raise HTTPException(
            status_code=404,
            detail={
                "type": "ORDER_NOT_FOUND",
                "message": "Order not found for support escalation.",
                "order_id": order_id,
            },
        )

    escalation_reason = (
        (payload.reason if payload else None)
        or reason
        or "Escalonamento manual para N2."
    )
    escalated_to = (payload.escalated_to if payload else "N2") or "N2"
    correlation_id = f"support-escalate-{uuid4().hex}"

    audit = record_ops_action_audit(
        db=db,
        action="SUPPORT_ESCALATE",
        result="SUCCESS",
        correlation_id=correlation_id,
        role="support_n1",
        order_id=order_id,
        details={
            "reason": escalation_reason,
            "escalated_to": escalated_to,
            "order_status": _enum_value(order.status),
        },
    )
    db.commit()

    return {
        "status": "escalated",
        "level": escalated_to,
        "escalated_to": escalated_to,
        "order_id": order_id,
        "reason": escalation_reason,
        "audit_id": audit.id,
        "correlation_id": correlation_id,
    }
