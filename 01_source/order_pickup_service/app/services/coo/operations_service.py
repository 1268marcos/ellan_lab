"""Operações — dashboard consolidado, saúde de pickups, deadlines, aprovações (stub fila)."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.allocation import Allocation, AllocationState
from app.models.locker import Locker
from app.models.order import Order, OrderStatus
from app.models.pickup import Pickup, PickupLifecycleStage, PickupStatus
from app.schemas.coo import ApprovalAck, ApprovalRequest, DashboardSummary, OperationsHealth


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


_TERMINAL_ALLOC = {
    AllocationState.PICKED_UP,
    AllocationState.EXPIRED,
    AllocationState.RELEASED,
    AllocationState.CANCELLED,
}


class OperationsService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_consolidated_dashboard(self, days: int) -> DashboardSummary:
        db = self._db
        now = _utc_now()
        horizon = max(1, min(int(days), 366))
        start = now - timedelta(days=horizon)

        orders_in_window = int(db.query(func.count(Order.id)).filter(Order.created_at >= start).scalar() or 0)

        active_allocations = int(
            db.query(func.count(Allocation.id)).filter(Allocation.state.notin_(list(_TERMINAL_ALLOC))).scalar() or 0
        )

        pending_pickup_allocations = int(
            db.query(func.count(Allocation.id))
            .filter(
                Allocation.state.in_(
                    [
                        AllocationState.RESERVED_PAID_PENDING_PICKUP,
                        AllocationState.OPENED_FOR_PICKUP,
                    ]
                )
            )
            .scalar()
            or 0
        )

        error_allocations = int(
            db.query(func.count(Allocation.id)).filter(Allocation.state == AllocationState.ERROR).scalar() or 0
        )

        lockers_total = int(db.query(func.count(Locker.id)).scalar() or 0)
        lockers_active = int(db.query(func.count(Locker.id)).filter(Locker.active.is_(True)).scalar() or 0)

        pickups_created = int(
            db.query(func.count(Pickup.id)).filter(Pickup.created_at >= start).scalar() or 0
        )
        pickups_redeemed = int(
            db.query(func.count(Pickup.id))
            .filter(
                Pickup.status == PickupStatus.REDEEMED,
                Pickup.redeemed_at.isnot(None),
                Pickup.redeemed_at >= start,
            )
            .scalar()
            or 0
        )
        p_rate = round(100.0 * float(pickups_redeemed) / float(pickups_created), 2) if pickups_created else 0.0

        avg_cycle = db.query(
            func.avg(func.extract("epoch", Pickup.redeemed_at - Pickup.activated_at) / 60.0),
        ).filter(
            Pickup.status == PickupStatus.REDEEMED,
            Pickup.redeemed_at.isnot(None),
            Pickup.activated_at.isnot(None),
            Pickup.redeemed_at >= start,
            Pickup.redeemed_at >= Pickup.activated_at,
        )
        avg_pickup_cycle_min = avg_cycle.scalar()
        avg_pickup_cycle_f = round(float(avg_pickup_cycle_min), 2) if avg_pickup_cycle_min is not None else None

        return DashboardSummary(
            horizon_days=horizon,
            as_of=now.isoformat(),
            orders_in_window=orders_in_window,
            active_allocations=active_allocations,
            pending_pickup_allocations=pending_pickup_allocations,
            error_allocations=error_allocations,
            lockers_total=lockers_total,
            lockers_active=lockers_active,
            pickups_created_in_window=pickups_created,
            pickups_redeemed_in_window=pickups_redeemed,
            pickup_completion_rate_pct=p_rate,
            avg_pickup_cycle_min=avg_pickup_cycle_f,
        )

    def get_pickup_health(self, region: str | None) -> OperationsHealth:
        db = self._db
        now = _utc_now()
        r_norm = region.strip().upper() if region else None

        q_pick_scope = db.query(func.count(Pickup.id)).outerjoin(Locker, Pickup.locker_id == Locker.id)
        if r_norm:
            q_pick_scope = q_pick_scope.filter(or_(Pickup.region == r_norm, Locker.region == r_norm))
        pickups_in_scope = int(q_pick_scope.scalar() or 0)

        if pickups_in_scope > 0:

            def _pickup_count(*extra_filters: Any) -> int:
                q = db.query(func.count(Pickup.id)).outerjoin(Locker, Pickup.locker_id == Locker.id)
                if r_norm:
                    q = q.filter(or_(Pickup.region == r_norm, Locker.region == r_norm))
                for f in extra_filters:
                    q = q.filter(f)
                return int(q.scalar() or 0)

            pending = _pickup_count(
                Pickup.status == PickupStatus.ACTIVE,
                Pickup.lifecycle_stage.in_(
                    [PickupLifecycleStage.CREATED, PickupLifecycleStage.READY_FOR_PICKUP],
                ),
            )
            opened = _pickup_count(
                Pickup.status == PickupStatus.ACTIVE,
                Pickup.lifecycle_stage.in_(
                    [
                        PickupLifecycleStage.DOOR_OPENED,
                        PickupLifecycleStage.ITEM_REMOVED,
                        PickupLifecycleStage.DOOR_CLOSED,
                    ],
                ),
            )
            fail_horizon = now - timedelta(days=7)
            errors = _pickup_count(
                Pickup.status.in_([PickupStatus.EXPIRED, PickupStatus.CANCELLED]),
                Pickup.updated_at >= fail_horizon,
            )
        else:
            q_pending = db.query(func.count(Allocation.id)).join(Locker, Allocation.locker_id == Locker.id)
            q_errors = db.query(func.count(Allocation.id)).join(Locker, Allocation.locker_id == Locker.id)
            q_open = db.query(func.count(Allocation.id)).join(Locker, Allocation.locker_id == Locker.id)

            if r_norm:
                q_pending = q_pending.filter(Locker.region == r_norm)
                q_errors = q_errors.filter(Locker.region == r_norm)
                q_open = q_open.filter(Locker.region == r_norm)

            pending = int(
                q_pending.filter(Allocation.state == AllocationState.RESERVED_PAID_PENDING_PICKUP).scalar() or 0
            )
            opened = int(q_open.filter(Allocation.state == AllocationState.OPENED_FOR_PICKUP).scalar() or 0)
            errors = int(q_errors.filter(Allocation.state == AllocationState.ERROR).scalar() or 0)

        denom = max(1, pending + opened + errors)
        health_score = round(100.0 * (1.0 - (errors / denom)), 2)

        return OperationsHealth(
            region=r_norm,
            pending_pickup=pending,
            opened_for_pickup=opened,
            errors=errors,
            health_score=min(100.0, max(0.0, health_score)),
            as_of=now.isoformat(),
        )

    def get_urgent_deadlines(self, limit: int) -> list[dict[str, Any]]:
        db = self._db
        now = _utc_now()
        horizon = now + timedelta(hours=2)
        lim = max(1, min(int(limit), 500))

        rows = (
            db.query(Order)
            .filter(
                Order.pickup_deadline_at.isnot(None),
                Order.pickup_deadline_at >= now,
                Order.pickup_deadline_at <= horizon,
                Order.status.in_([OrderStatus.PAID_PENDING_PICKUP, OrderStatus.DISPENSED]),
            )
            .order_by(Order.pickup_deadline_at.asc())
            .limit(lim)
            .all()
        )

        result: list[dict[str, Any]] = []
        for o in rows:
            ddl = o.pickup_deadline_at
            result.append(
                {
                    "order_id": str(o.id),
                    "pickup_deadline_at": ddl.isoformat() if ddl else None,
                    "status": o.status.value if hasattr(o.status, "value") else str(o.status),
                    "source": "order_deadline",
                }
            )

        p_rows = (
            db.query(Pickup)
            .filter(
                Pickup.status == PickupStatus.ACTIVE,
                Pickup.expires_at.isnot(None),
                Pickup.expires_at >= now,
                Pickup.expires_at <= horizon,
            )
            .order_by(Pickup.expires_at.asc())
            .limit(max(1, lim - len(result)))
            .all()
        )
        for p in p_rows:
            ddl = p.expires_at
            remaining_min = int((ddl - now).total_seconds() / 60) if ddl else 0
            result.append(
                {
                    "pickup_id": str(p.id),
                    "order_id": str(p.order_id),
                    "locker_id": p.locker_id,
                    "pickup_deadline_at": ddl.isoformat() if ddl else None,
                    "time_remaining_min": remaining_min,
                    "status": p.status.value if hasattr(p.status, "value") else str(p.status),
                    "source": "pickup_expires_at",
                }
            )
        return result[:lim]

    def get_pending_approvals(self, approval_type: str | None) -> list[dict[str, Any]]:
        items = [
            {
                "id": "APP-001",
                "approval_type": "sla_adjustment",
                "requester": "Região Sul",
                "created_at": _utc_now().isoformat(),
                "details": {"region": "sul", "new_sla_minutes": 45, "current_sla_minutes": 60},
            },
            {
                "id": "APP-002",
                "approval_type": "expansion",
                "requester": "Norte Shopping",
                "created_at": (_utc_now() - timedelta(days=1)).isoformat(),
                "details": {"location": "Norte Shopping", "lockers_requested": 5, "estimated_cost": 25000},
            },
        ]
        if approval_type:
            items = [i for i in items if i.get("approval_type") == approval_type]
        return [
            {
                "approval_type": approval_type or "ANY",
                "pending_count": len(items),
                "items": items,
                "note": "Itens de demonstração até fila de aprovações persistida.",
            }
        ]

    def submit_sla_adjustment(self, request: ApprovalRequest) -> ApprovalAck:
        del request  # payload reservado
        return ApprovalAck(
            status="QUEUED",
            approval_id=str(uuid.uuid4()),
            message="Ajuste de SLA enfileirado (stub COO).",
        )

    def submit_expansion_request(self, request: ApprovalRequest) -> ApprovalAck:
        del request
        return ApprovalAck(
            status="QUEUED",
            approval_id=str(uuid.uuid4()),
            message="Expansion request enfileirado (stub COO).",
        )
