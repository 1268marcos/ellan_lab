# 01_source/order_pickup_service/app/routers/dev_admin.py
# 15/04/2026 - nova @router.post("/simulate-online-payment") - foi substituída em 17/04/2026
# 17/04/2026 - nova @router.post("/simulate-online-payment")
# 18/04/2026 - remoção : from app.routers.internal import _ensure_online_pickup, _create_pickup_token
# 18/04/2026 - remoção : from app.routers.internal import _ensure_online_pickup
# 18/04/2026 - inclusão : from app.services.pickup_payment_fulfillment_service import _create_pickup_token, _ensure_online_pickup
# 20/04/2026 - compensação para não deixar slot preso

from __future__ import annotations

import logging
import csv
import io
import json

from typing import Any

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.auth_dep import get_current_user, require_user_roles
from app.core.config import settings
from app.core.db import SessionLocal, get_db

from app.models.order import Order, OrderStatus
from app.models.pickup import Pickup
from app.models.user import User
from app.schemas.dev_admin import (
    DevOpsErrorInvestigationReportOut,
    DevOrderStatusAuditItemOut,
    DevOrderStatusAuditListOut,
    DevOrderStatusAuditPagedOut,
    DevOpsAuditItemOut,
    DevOpsAuditListOut,
    DevOpsMetricsOut,
    DevOpsPredictiveSnapshotIn,
    DevOpsPredictiveSnapshotOut,
    DevReconcileOrderIn,
    DevReconciliationPendingItemOut,
    DevReconciliationPendingListOut,
    DevReconcileOrderOut,
    DevReleaseRegionalAllocationsIn,
    DevReleaseRegionalAllocationsOut,
    DevResetLockerIn,
    DevResetLockerOut,
)
from app.services import backend_client

from uuid import uuid4


from app.models.allocation import Allocation, AllocationState
from app.models.pickup import Pickup, PickupStatus, PickupLifecycleStage, PickupChannel
from app.models.pickup_token import PickupToken

from app.services.payment_confirm_service import apply_payment_confirmation

from app.services.pickup_payment_fulfillment_service import (
    _create_pickup_token,
    _ensure_online_pickup,
    fulfill_payment_post_approval,
)
from app.services.order_reconciliation_service import (
    reconcile_order_compensation,
    resolve_latest_allocation,
    resolve_latest_pickup,
)
from app.services.reconciliation_pending_service import list_reconciliation_pending
from app.jobs.reconciliation_retry import run_reconciliation_retry_once
from app.services.ops_audit_service import list_ops_action_audit, record_ops_action_audit
from app.services.ops_metrics_service import build_ops_metrics, build_ops_error_investigation_report

from app.routers.internal import _ensure_allocation

from app.core.datetime_utils import to_iso_utc



logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/dev-admin",
    tags=["dev-admin"],
    dependencies=[Depends(require_user_roles(allowed_roles={"admin_operacao", "auditoria"}))],
)

#-------------------------------------
# HELPERS
#-------------------------------------
def _sha256(s: str) -> str:
    import hashlib
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def _generate_manual_code() -> str:
    return f"{uuid4().int % 1_000_000:06d}"


def _ensure_dev_mode() -> None:
    if not settings.dev_bypass_auth:
        raise HTTPException(
            status_code=403,
            detail={
                "type": "DEV_MODE_REQUIRED",
                "message": "Este endpoint só pode ser usado com VITE_DEV_BYPASS_AUTH=true. Veja 01_source/order_pickup_service/.env",
            },
        )


def _normalize_region(value: str) -> str:
    region = str(value or "").strip().upper()
    if region not in {"SP", "PT"}:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "INVALID_REGION",
                "message": "region deve ser SP ou PT.",
            },
        )
    return region


def _validate_locker_region(*, region: str, locker_id: str) -> dict:
    locker = backend_client.get_locker_registry_item(locker_id)
    if not locker:
        raise HTTPException(
            status_code=404,
            detail={
                "type": "LOCKER_NOT_FOUND",
                "message": f"Locker não encontrado: {locker_id}",
                "locker_id": locker_id,
            },
        )

    locker_region = str(locker.get("region") or "").strip().upper()
    if locker_region != region:
        raise HTTPException(
            status_code=409,
            detail={
                "type": "LOCKER_REGION_MISMATCH",
                "message": "O locker informado não pertence à região enviada.",
                "locker_id": locker_id,
                "payload_region": region,
                "locker_region": locker_region,
            },
        )

    return locker


def _resolve_effective_pickup_deadline(db: Session, *, order: Order) -> tuple[datetime | None, str | None]:
    deadline = getattr(order, "pickup_deadline_at", None)
    if deadline is not None:
        return deadline, "order.pickup_deadline_at"

    latest_pickup = (
        db.query(Pickup)
        .filter(Pickup.order_id == order.id)
        .order_by(Pickup.created_at.desc(), Pickup.id.desc())
        .first()
    )
    if latest_pickup and getattr(latest_pickup, "expires_at", None):
        return latest_pickup.expires_at, "pickup.expires_at"
    return None, None


def _assert_order_reconciliation_allowed(db: Session, *, order: Order) -> None:
    allowed_statuses = {
        OrderStatus.PAYMENT_PENDING,
        OrderStatus.FAILED,
        OrderStatus.CANCELLED,
        OrderStatus.EXPIRED,
        OrderStatus.EXPIRED_CREDIT_50,
    }
    if order.status in allowed_statuses:
        return

    if order.status == OrderStatus.PAID_PENDING_PICKUP:
        deadline, deadline_source = _resolve_effective_pickup_deadline(db, order=order)
        now = datetime.now(timezone.utc)

        if deadline is None:
            raise HTTPException(
                status_code=409,
                detail={
                    "type": "RECONCILIATION_NOT_ALLOWED",
                    "message": (
                        "Pedido em status PAID_PENDING_PICKUP sem deadline efetivo "
                        "(order/pickup) não pode ser reconciliado por segurança."
                    ),
                    "current_status": order.status.value,
                },
            )

        if getattr(deadline, "tzinfo", None) is None:
            deadline = deadline.replace(tzinfo=timezone.utc)

        if deadline > now:
            raise HTTPException(
                status_code=409,
                detail={
                    "type": "RECONCILIATION_NOT_ALLOWED",
                    "message": (
                        "Pedido em status PAID_PENDING_PICKUP ainda dentro do prazo de retirada "
                        "não pode ser reconciliado."
                    ),
                    "current_status": order.status.value,
                    "effective_deadline_at": to_iso_utc(deadline),
                    "effective_deadline_source": deadline_source,
                },
            )
        return

    raise HTTPException(
        status_code=409,
        detail={
            "type": "RECONCILIATION_NOT_ALLOWED",
            "message": f"Pedido em status {order.status.value} não pode ser reconciliado.",
            "current_status": order.status.value,
        },
    )


def _resolve_correlation_id(header_value: str | None) -> str:
    value = str(header_value or "").strip()
    return value or str(uuid4())


def _coerce_audit_details(details_raw: Any) -> dict[str, Any]:
    if isinstance(details_raw, dict):
        return details_raw
    if isinstance(details_raw, str):
        raw = details_raw.strip()
        if not raw:
            return {}
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def _parse_iso_datetime_utc(raw_value: str, *, field_name: str) -> datetime:
    value = str(raw_value or "").strip()
    if not value:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "INVALID_DATE_RANGE",
                "message": f"{field_name} é obrigatório.",
                "field": field_name,
            },
        )
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "INVALID_DATE_RANGE",
                "message": f"{field_name} inválido. Use ISO-8601.",
                "field": field_name,
                "value": value,
            },
        ) from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _collect_orders_status_audit(
    *,
    db: Session,
    created_from: datetime,
    created_to: datetime,
    limit: int,
    offset: int = 0,
) -> tuple[list[DevOrderStatusAuditItemOut], int]:
    order_query = (
        db.query(Order)
        .filter(
            Order.created_at >= created_from,
            Order.created_at <= created_to,
        )
        .order_by(Order.created_at.desc(), Order.id.desc())
    )
    candidate_orders = order_query.offset(offset).limit(limit + 1).all()

    items: list[DevOrderStatusAuditItemOut] = []
    for order in candidate_orders:
        pickup = (
            db.query(Pickup)
            .filter(Pickup.order_id == order.id)
            .order_by(Pickup.created_at.desc(), Pickup.id.desc())
            .first()
        )

        reasons: list[str] = []
        if order.picked_up_at is not None and order.status in {OrderStatus.EXPIRED, OrderStatus.EXPIRED_CREDIT_50}:
            reasons.append("picked_up_at_not_null_but_order_expired")
        if order.status == OrderStatus.DISPENSED and pickup is not None and pickup.status == PickupStatus.EXPIRED:
            reasons.append("order_dispensed_but_pickup_expired")
        if order.status in {OrderStatus.EXPIRED, OrderStatus.EXPIRED_CREDIT_50} and pickup is not None and pickup.status == PickupStatus.REDEEMED:
            reasons.append("order_expired_but_pickup_redeemed")
        if not reasons:
            continue

        items.append(
            DevOrderStatusAuditItemOut(
                order_id=order.id,
                order_status=order.status.value if order.status else "",
                payment_status=order.payment_status.value if order.payment_status else None,
                paid_at=to_iso_utc(order.paid_at),
                picked_up_at=to_iso_utc(order.picked_up_at),
                pickup_deadline_at=to_iso_utc(order.pickup_deadline_at),
                pickup_status=(pickup.status.value if pickup and pickup.status else None),
                pickup_lifecycle_stage=(
                    pickup.lifecycle_stage.value
                    if pickup and getattr(pickup, "lifecycle_stage", None)
                    else None
                ),
                pickup_id=(pickup.id if pickup else None),
                reason=";".join(reasons),
            )
        )

    return items[:limit], len(candidate_orders)


def _safe_record_ops_audit(
    *,
    action: str,
    result: str,
    correlation_id: str,
    user_id: str | None = None,
    role: str | None = None,
    order_id: str | None = None,
    error_message: str | None = None,
    details: dict | None = None,
) -> None:
    db = SessionLocal()
    try:
        record_ops_action_audit(
            db=db,
            action=action,
            result=result,
            correlation_id=correlation_id,
            user_id=user_id,
            role=role,
            order_id=order_id,
            error_message=error_message,
            details=details or {},
        )
        db.commit()
    except Exception:
        db.rollback()
        logger.exception(
            "ops_audit_write_failed action=%s correlation_id=%s order_id=%s",
            action,
            correlation_id,
            order_id,
        )
    finally:
        db.close()


@router.post("/reconcile-order", response_model=DevReconcileOrderOut)
def dev_reconcile_order(
    payload: DevReconcileOrderIn,
    current_user: User = Depends(get_current_user),
    correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    db: Session = Depends(get_db),
):
    corr_id = _resolve_correlation_id(correlation_id)
    order_id = str(payload.order_id or "").strip()
    try:
        if not order_id:
            raise HTTPException(
                status_code=400,
                detail={
                    "type": "ORDER_ID_REQUIRED",
                    "message": "order_id é obrigatório.",
                },
            )

        order = db.get(Order, order_id)
        if not order:
            raise HTTPException(
                status_code=404,
                detail={
                    "type": "ORDER_NOT_FOUND",
                    "message": "Pedido não encontrado.",
                    "order_id": order_id,
                },
            )

        _assert_order_reconciliation_allowed(db, order=order)

        allocation = resolve_latest_allocation(db, order=order)
        pickup = resolve_latest_pickup(db, order=order)
        compensation = reconcile_order_compensation(
            db=db,
            order=order,
            allocation=allocation,
            pickup=pickup,
            cancel_reason="ops_order_reconciliation",
        )

        if order.status != OrderStatus.CANCELLED:
            order.mark_as_cancelled()
        else:
            order.touch()

        db.commit()
        _safe_record_ops_audit(
            action="OPS_RECONCILE_ORDER",
            result="SUCCESS",
            correlation_id=corr_id,
            user_id=current_user.id,
            role="ops_user",
            order_id=order.id,
            details={
                "status": order.status.value,
                "slot_release_ok": compensation.slot_release_ok,
                "credit_restored": compensation.credit_restored,
            },
        )

        return DevReconcileOrderOut(
            ok=True,
            order_id=order.id,
            status=order.status.value,
            message="Reconciliação operacional executada com sucesso.",
            compensation={
                "credit_restored": compensation.credit_restored,
                "credit_restore_error": compensation.credit_restore_error,
                "slot_release_attempted": compensation.slot_release_attempted,
                "slot_release_ok": compensation.slot_release_ok,
                "slot_release_error": compensation.slot_release_error,
                "allocation_id": compensation.allocation_id,
                "allocation_state": compensation.allocation_state,
            },
        )
    except HTTPException as exc:
        detail_message = (
            str(exc.detail.get("message"))
            if isinstance(exc.detail, dict) and exc.detail.get("message")
            else str(exc.detail)
        )
        _safe_record_ops_audit(
            action="OPS_RECONCILE_ORDER",
            result="ERROR",
            correlation_id=corr_id,
            user_id=current_user.id if current_user else None,
            role="ops_user",
            order_id=order_id or None,
            error_message=detail_message,
            details={"status_code": exc.status_code},
        )
        raise
    except Exception as exc:
        _safe_record_ops_audit(
            action="OPS_RECONCILE_ORDER",
            result="ERROR",
            correlation_id=corr_id,
            user_id=current_user.id if current_user else None,
            role="ops_user",
            order_id=order_id or None,
            error_message=str(exc),
        )
        raise


@router.get("/reconciliation-pending", response_model=DevReconciliationPendingListOut)
def dev_reconciliation_pending_list(
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    db: Session = Depends(get_db),
):
    corr_id = _resolve_correlation_id(correlation_id)
    rows = list_reconciliation_pending(db, status=status, limit=limit)
    items = [
        DevReconciliationPendingItemOut(
            id=row.id,
            order_id=row.order_id,
            reason=row.reason,
            status=row.status,
            attempt_count=int(row.attempt_count or 0),
            max_attempts=int(row.max_attempts or 0),
            next_retry_at=to_iso_utc(row.next_retry_at),
            last_error=row.last_error,
            updated_at=to_iso_utc(row.updated_at),
        )
        for row in rows
    ]
    response = DevReconciliationPendingListOut(
        ok=True,
        total=len(items),
        items=items,
    )
    _safe_record_ops_audit(
        action="OPS_RECON_PENDING_LIST",
        result="SUCCESS",
        correlation_id=corr_id,
        user_id=current_user.id,
        role="ops_user",
        details={"status_filter": status, "limit": limit, "returned": len(items)},
    )
    return response


@router.post("/reconciliation-pending/run-once")
def dev_reconciliation_pending_run_once(
    batch_size: int = Query(default=25, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    db: Session = Depends(get_db),
):
    corr_id = _resolve_correlation_id(correlation_id)
    processed = run_reconciliation_retry_once(db, batch_size=batch_size)
    _safe_record_ops_audit(
        action="OPS_RECON_PENDING_RUN_ONCE",
        result="SUCCESS",
        correlation_id=corr_id,
        user_id=current_user.id,
        role="ops_user",
        details={"batch_size": batch_size, "processed": int(processed or 0)},
    )
    return {
        "ok": True,
        "processed": int(processed or 0),
        "message": "Processamento manual de pendências executado.",
    }


@router.get("/ops-audit", response_model=DevOpsAuditListOut)
def dev_ops_audit_list(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    order_id: str | None = Query(default=None),
    action: str | None = Query(default=None),
    result: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    db: Session = Depends(get_db),
):
    corr_id = _resolve_correlation_id(correlation_id)
    rows = list_ops_action_audit(
        db=db,
        limit=limit,
        offset=offset,
        order_id=order_id,
        action=action,
        result=result,
    )
    items = [
        DevOpsAuditItemOut(
            id=row.id,
            action=row.action,
            result=row.result,
            correlation_id=row.correlation_id,
            user_id=row.user_id,
            role=row.role,
            order_id=row.order_id,
            error_message=row.error_message,
            details=_coerce_audit_details(row.details_json),
            created_at=to_iso_utc(row.created_at),
        )
        for row in rows
    ]
    _safe_record_ops_audit(
        action="OPS_AUDIT_LIST",
        result="SUCCESS",
        correlation_id=corr_id,
        user_id=current_user.id,
        role="ops_user",
        details={
            "limit": limit,
            "offset": offset,
            "order_id": order_id,
            "action_filter": action,
            "result_filter": result,
            "returned": len(items),
        },
    )
    return DevOpsAuditListOut(ok=True, total=len(items), items=items)


@router.get("/ops-metrics", response_model=DevOpsMetricsOut)
def dev_ops_metrics(
    lookback_hours: int = Query(default=settings.ops_metrics_lookback_hours, ge=1, le=168),
    pending_open_threshold: int = Query(
        default=settings.ops_alert_pending_open_threshold,
        ge=1,
        le=10000,
    ),
    error_rate_threshold: float = Query(
        default=settings.ops_alert_error_rate_threshold,
        ge=0.0,
        le=1.0,
    ),
    failed_final_threshold: int = Query(
        default=settings.ops_alert_failed_final_threshold,
        ge=1,
        le=10000,
    ),
    predictive_min_volume: int = Query(default=5, ge=1, le=500),
    predictive_error_min_rate: float = Query(default=0.05, ge=0.0, le=1.0),
    predictive_error_accel_factor: float = Query(default=1.5, ge=1.0, le=10.0),
    predictive_latency_min_ms: float = Query(default=100.0, ge=0.0, le=60000.0),
    predictive_latency_accel_factor: float = Query(default=1.4, ge=1.0, le=10.0),
    current_user: User = Depends(get_current_user),
    correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    db: Session = Depends(get_db),
):
    corr_id = _resolve_correlation_id(correlation_id)
    metrics = build_ops_metrics(
        db=db,
        lookback_hours=lookback_hours,
        pending_open_threshold=pending_open_threshold,
        error_rate_threshold=error_rate_threshold,
        failed_final_threshold=failed_final_threshold,
        predictive_min_volume=predictive_min_volume,
        predictive_error_min_rate=predictive_error_min_rate,
        predictive_error_accel_factor=predictive_error_accel_factor,
        predictive_latency_min_ms=predictive_latency_min_ms,
        predictive_latency_accel_factor=predictive_latency_accel_factor,
    )
    _safe_record_ops_audit(
        action="OPS_METRICS_VIEW",
        result="SUCCESS",
        correlation_id=corr_id,
        user_id=current_user.id,
        role="ops_user",
        details={
            "lookback_hours": lookback_hours,
            "pending_open_threshold": pending_open_threshold,
            "error_rate_threshold": error_rate_threshold,
            "failed_final_threshold": failed_final_threshold,
            "predictive_min_volume": predictive_min_volume,
            "predictive_error_min_rate": predictive_error_min_rate,
            "predictive_error_accel_factor": predictive_error_accel_factor,
            "predictive_latency_min_ms": predictive_latency_min_ms,
            "predictive_latency_accel_factor": predictive_latency_accel_factor,
            "alerts_count": len(metrics.get("alerts", [])),
        },
    )
    return DevOpsMetricsOut.model_validate(
        {
            "ok": True,
            **metrics,
        }
    )


@router.post("/ops-metrics/predictive-snapshots", response_model=DevOpsPredictiveSnapshotOut)
def dev_ops_metrics_predictive_snapshot_create(
    payload: DevOpsPredictiveSnapshotIn,
    current_user: User = Depends(get_current_user),
    correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    db: Session = Depends(get_db),
):
    corr_id = _resolve_correlation_id(correlation_id)
    thresholds = {
        "predictive_min_volume": int(payload.predictive_min_volume or 5),
        "predictive_error_min_rate": float(payload.predictive_error_min_rate or 0.05),
        "predictive_error_accel_factor": float(payload.predictive_error_accel_factor or 1.5),
        "predictive_latency_min_ms": float(payload.predictive_latency_min_ms or 100.0),
        "predictive_latency_accel_factor": float(payload.predictive_latency_accel_factor or 1.4),
    }
    metrics = build_ops_metrics(
        db=db,
        lookback_hours=168,
        predictive_min_volume=thresholds["predictive_min_volume"],
        predictive_error_min_rate=thresholds["predictive_error_min_rate"],
        predictive_error_accel_factor=thresholds["predictive_error_accel_factor"],
        predictive_latency_min_ms=thresholds["predictive_latency_min_ms"],
        predictive_latency_accel_factor=thresholds["predictive_latency_accel_factor"],
    )
    monitoring = metrics.get("predictive_monitoring") if isinstance(metrics, dict) else {}
    details = {
        "environment": str(payload.environment or "hml").lower(),
        "decision": str(payload.decision or "KEEP").upper(),
        "rationale": payload.rationale,
        "thresholds": thresholds,
        "monitoring": {
            "emitted_alerts": int((monitoring or {}).get("emitted_alerts") or 0),
            "confirmed_alerts": int((monitoring or {}).get("confirmed_alerts") or 0),
            "false_positive_alerts": int((monitoring or {}).get("false_positive_alerts") or 0),
            "false_positive_rate": float((monitoring or {}).get("false_positive_rate") or 0.0),
        },
        "window": metrics.get("window") if isinstance(metrics, dict) else {},
    }
    row = record_ops_action_audit(
        db=db,
        action="OPS_PREDICTIVE_WEEKLY_SNAPSHOT",
        result="SUCCESS",
        correlation_id=corr_id,
        user_id=current_user.id,
        role="ops_user",
        details=details,
    )
    db.commit()
    return DevOpsPredictiveSnapshotOut.model_validate(
        {
            "id": row.id,
            "created_at": to_iso_utc(row.created_at),
            "environment": details["environment"],
            "decision": details["decision"],
            "rationale": details.get("rationale"),
            "false_positive_rate": details["monitoring"]["false_positive_rate"],
            "emitted_alerts": details["monitoring"]["emitted_alerts"],
            "confirmed_alerts": details["monitoring"]["confirmed_alerts"],
            "false_positive_alerts": details["monitoring"]["false_positive_alerts"],
            "thresholds": thresholds,
        }
    )


@router.get("/ops-metrics/error-investigation", response_model=DevOpsErrorInvestigationReportOut)
def dev_ops_metrics_error_investigation(
    lookback_hours: int = Query(default=settings.ops_metrics_lookback_hours, ge=1, le=24 * 30),
    top_causes_limit: int = Query(default=3, ge=1, le=10),
    evidence_per_cause_limit: int = Query(default=3, ge=1, le=10),
    current_user: User = Depends(get_current_user),
    correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    db: Session = Depends(get_db),
):
    corr_id = _resolve_correlation_id(correlation_id)
    report = build_ops_error_investigation_report(
        db=db,
        lookback_hours=lookback_hours,
        top_causes_limit=top_causes_limit,
        evidence_per_cause_limit=evidence_per_cause_limit,
    )
    _safe_record_ops_audit(
        action="OPS_ERROR_INVESTIGATION_REPORT_VIEW",
        result="SUCCESS",
        correlation_id=corr_id,
        user_id=current_user.id,
        role="ops_user",
        details={
            "lookback_hours": lookback_hours,
            "top_causes_limit": top_causes_limit,
            "evidence_per_cause_limit": evidence_per_cause_limit,
            "total_error_actions": int(report.get("total_error_actions") or 0),
        },
    )
    return DevOpsErrorInvestigationReportOut.model_validate({"ok": True, **report})


@router.get("/ops-metrics/error-investigation/export.csv")
def dev_ops_metrics_error_investigation_export_csv(
    lookback_hours: int = Query(default=settings.ops_metrics_lookback_hours, ge=1, le=24 * 30),
    top_causes_limit: int = Query(default=3, ge=1, le=10),
    evidence_per_cause_limit: int = Query(default=3, ge=1, le=10),
    current_user: User = Depends(get_current_user),
    correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    db: Session = Depends(get_db),
):
    corr_id = _resolve_correlation_id(correlation_id)
    report = build_ops_error_investigation_report(
        db=db,
        lookback_hours=lookback_hours,
        top_causes_limit=top_causes_limit,
        evidence_per_cause_limit=evidence_per_cause_limit,
    )
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "window_from",
            "window_to",
            "total_error_actions",
            "category",
            "cause_message",
            "cause_count",
            "cause_percentage",
            "evidence_audit_id",
            "evidence_created_at",
            "evidence_correlation_id",
            "evidence_action",
        ]
    )
    categories = report.get("categories") if isinstance(report, dict) else []
    top_causes = report.get("top_causes") if isinstance(report, dict) else []
    window = report.get("window") if isinstance(report, dict) else {}
    window_from = str(window.get("from") or "")
    window_to = str(window.get("to") or "")
    total_error_actions = int(report.get("total_error_actions") or 0)

    if not top_causes and categories:
        for category_row in categories:
            writer.writerow(
                [
                    window_from,
                    window_to,
                    total_error_actions,
                    category_row.get("category"),
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                ]
            )
    else:
        for cause in top_causes:
            evidence_rows = cause.get("evidence") or [{}]
            for evidence in evidence_rows:
                writer.writerow(
                    [
                        window_from,
                        window_to,
                        total_error_actions,
                        cause.get("category"),
                        cause.get("message"),
                        cause.get("count"),
                        cause.get("percentage"),
                        evidence.get("audit_id") if isinstance(evidence, dict) else "",
                        evidence.get("created_at") if isinstance(evidence, dict) else "",
                        evidence.get("correlation_id") if isinstance(evidence, dict) else "",
                        evidence.get("action") if isinstance(evidence, dict) else "",
                    ]
                )

    output.seek(0)
    _safe_record_ops_audit(
        action="OPS_ERROR_INVESTIGATION_REPORT_EXPORT",
        result="SUCCESS",
        correlation_id=corr_id,
        user_id=current_user.id,
        role="ops_user",
        details={
            "lookback_hours": lookback_hours,
            "top_causes_limit": top_causes_limit,
            "evidence_per_cause_limit": evidence_per_cause_limit,
            "total_error_actions": total_error_actions,
        },
    )
    filename = f"ops_error_investigation_{lookback_hours}h.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/orders-status-audit", response_model=DevOrderStatusAuditListOut)
def dev_orders_status_audit(
    lookback_hours: int = Query(default=48, ge=1, le=24 * 30),
    limit: int = Query(default=200, ge=1, le=2000),
    current_user: User = Depends(get_current_user),
    correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    db: Session = Depends(get_db),
):
    corr_id = _resolve_correlation_id(correlation_id)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    items, _ = _collect_orders_status_audit(
        db=db,
        created_from=cutoff,
        created_to=datetime.now(timezone.utc),
        limit=limit,
        offset=0,
    )

    _safe_record_ops_audit(
        action="OPS_ORDERS_STATUS_AUDIT",
        result="SUCCESS",
        correlation_id=corr_id,
        user_id=current_user.id,
        role="ops_user",
        details={
            "lookback_hours": lookback_hours,
            "limit": limit,
            "returned": len(items),
        },
    )

    return DevOrderStatusAuditListOut(ok=True, total=len(items), items=items)


@router.get("/orders-status-audit/range", response_model=DevOrderStatusAuditPagedOut)
def dev_orders_status_audit_range(
    from_: str = Query(..., alias="from"),
    to: str = Query(...),
    limit: int = Query(default=200, ge=1, le=2000),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    db: Session = Depends(get_db),
):
    corr_id = _resolve_correlation_id(correlation_id)
    created_from = _parse_iso_datetime_utc(from_, field_name="from")
    created_to = _parse_iso_datetime_utc(to, field_name="to")
    if created_from > created_to:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "INVALID_DATE_RANGE",
                "message": "from deve ser menor ou igual a to.",
            },
        )

    items, fetched_count = _collect_orders_status_audit(
        db=db,
        created_from=created_from,
        created_to=created_to,
        limit=limit,
        offset=offset,
    )
    has_more = fetched_count > limit

    _safe_record_ops_audit(
        action="OPS_ORDERS_STATUS_AUDIT_RANGE",
        result="SUCCESS",
        correlation_id=corr_id,
        user_id=current_user.id,
        role="ops_user",
        details={
            "from": to_iso_utc(created_from),
            "to": to_iso_utc(created_to),
            "limit": limit,
            "offset": offset,
            "returned": len(items),
            "has_more": has_more,
        },
    )

    return DevOrderStatusAuditPagedOut.model_validate(
        {
            "ok": True,
            "total": len(items),
            "limit": limit,
            "offset": offset,
            "has_more": has_more,
            "from": to_iso_utc(created_from),
            "to": to_iso_utc(created_to),
            "items": items,
        }
    )


@router.get("/orders-status-audit/export.csv")
def dev_orders_status_audit_export_csv(
    from_: str = Query(..., alias="from"),
    to: str = Query(...),
    limit: int = Query(default=5000, ge=1, le=20000),
    current_user: User = Depends(get_current_user),
    correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    db: Session = Depends(get_db),
):
    corr_id = _resolve_correlation_id(correlation_id)
    created_from = _parse_iso_datetime_utc(from_, field_name="from")
    created_to = _parse_iso_datetime_utc(to, field_name="to")
    if created_from > created_to:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "INVALID_DATE_RANGE",
                "message": "from deve ser menor ou igual a to.",
            },
        )

    items, _ = _collect_orders_status_audit(
        db=db,
        created_from=created_from,
        created_to=created_to,
        limit=limit,
        offset=0,
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "order_id",
            "order_status",
            "payment_status",
            "paid_at",
            "picked_up_at",
            "pickup_deadline_at",
            "pickup_status",
            "pickup_lifecycle_stage",
            "pickup_id",
            "reason",
        ]
    )
    for item in items:
        writer.writerow(
            [
                item.order_id,
                item.order_status,
                item.payment_status or "",
                item.paid_at or "",
                item.picked_up_at or "",
                item.pickup_deadline_at or "",
                item.pickup_status or "",
                item.pickup_lifecycle_stage or "",
                item.pickup_id or "",
                item.reason,
            ]
        )
    output.seek(0)

    _safe_record_ops_audit(
        action="OPS_ORDERS_STATUS_AUDIT_EXPORT",
        result="SUCCESS",
        correlation_id=corr_id,
        user_id=current_user.id,
        role="ops_user",
        details={
            "from": to_iso_utc(created_from),
            "to": to_iso_utc(created_to),
            "limit": limit,
            "returned": len(items),
        },
    )

    filename = (
        f"orders_status_audit_{created_from.strftime('%Y%m%dT%H%M%SZ')}"
        f"_{created_to.strftime('%Y%m%dT%H%M%SZ')}.csv"
    )
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/release-regional-allocations", response_model=DevReleaseRegionalAllocationsOut)
def dev_release_regional_allocations(
    payload: DevReleaseRegionalAllocationsIn,
    db: Session = Depends(get_db),
):
    _ensure_dev_mode()

    region = _normalize_region(payload.region)
    locker_id = str(payload.locker_id or "").strip()
    if not locker_id:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "LOCKER_ID_REQUIRED",
                "message": "locker_id é obrigatório.",
            },
        )

    _validate_locker_region(region=region, locker_id=locker_id)

    allocation_ids = [
        str(item or "").strip()
        for item in (payload.allocation_ids or [])
        if str(item or "").strip()
    ]

    if not allocation_ids and payload.auto_collect_from_local_db:
        allocations = (
            db.query(Allocation)
            .join(Order, Order.id == Allocation.order_id)
            .filter(
                Allocation.locker_id == locker_id,
                Order.region == region,
            )
            .order_by(Allocation.created_at.asc(), Allocation.id.asc())
            .all()
        )

        allocation_ids = list(dict.fromkeys([
            str(allocation.id).strip()
            for allocation in allocations
            if str(allocation.id or "").strip()
        ]))

    if not allocation_ids:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "ALLOCATION_IDS_REQUIRED",
                "message": (
                    "Informe ao menos um allocation_id para liberação regional "
                    "ou mantenha auto_collect_from_local_db=true com allocations locais existentes."
                ),
            },
        )

    results: list[dict[str, Any]] = []
    released_count = 0
    failed_count = 0

    for allocation_id in allocation_ids:
        try:
            response = backend_client.locker_release(
                region=region,
                allocation_id=allocation_id,
                locker_id=locker_id,
            )
            results.append(
                {
                    "allocation_id": allocation_id,
                    "ok": True,
                    "response": response,
                }
            )
            released_count += 1
        except Exception as exc:
            results.append(
                {
                    "allocation_id": allocation_id,
                    "ok": False,
                    "error": str(exc),
                }
            )
            failed_count += 1

    return DevReleaseRegionalAllocationsOut(
        ok=failed_count == 0,
        region=region,
        locker_id=locker_id,
        results=results,
        released_count=released_count,
        failed_count=failed_count,
        message=(
            "Liberação DEV das allocations regionais concluída. "
            "Use isso para limpar conflitos órfãos do backend regional."
        ),
    )


@router.post("/reset-locker", response_model=DevResetLockerOut)
def dev_reset_locker(
    payload: DevResetLockerIn,
    db: Session = Depends(get_db),
):
    _ensure_dev_mode()

    region = _normalize_region(payload.region)
    locker_id = str(payload.locker_id or "").strip()
    if not locker_id:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "LOCKER_ID_REQUIRED",
                "message": "locker_id é obrigatório.",
            },
        )

    locker = _validate_locker_region(region=region, locker_id=locker_id)
    slots_total = int(locker.get("slots") or 24)

    released_allocations: list[str] = []
    slot_reset_results: list[dict[str, Any]] = []

    allocations = (
        db.query(Allocation)
        .join(Order, Order.id == Allocation.order_id)
        .filter(
            Allocation.locker_id == locker_id,
            Order.region == region,
        )
        .order_by(Allocation.created_at.asc(), Allocation.id.asc())
        .all()
    )

    try:
        if payload.release_known_allocations_first:
            for allocation in allocations:
                try:
                    backend_client.locker_release(
                        region=region,
                        allocation_id=allocation.id,
                        locker_id=locker_id,
                    )

                    if not payload.purge_local_data:
                        allocation.mark_released()

                    released_allocations.append(allocation.id)
                except Exception as exc:
                    released_allocations.append(f"{allocation.id} (erro: {str(exc)})")

        if not payload.purge_local_data:
            db.flush()

        for slot in range(1, slots_total + 1):
            try:
                response = backend_client.locker_set_state(
                    region=region,
                    slot=slot,
                    state="AVAILABLE",
                    locker_id=locker_id,
                )
                slot_reset_results.append(
                    {
                        "slot": slot,
                        "ok": True,
                        "response": response,
                    }
                )
            except Exception as exc:
                slot_reset_results.append(
                    {
                        "slot": slot,
                        "ok": False,
                        "error": str(exc),
                    }
                )

        deleted_pickups = 0
        deleted_allocations = 0
        deleted_orders = 0

        if payload.purge_local_data:
            order_ids = [
                row[0]
                for row in db.query(Order.id)
                .filter(Order.totem_id == locker_id, Order.region == region)
                .all()
            ]

            if order_ids:
                deleted_pickups = (
                    db.query(Pickup)
                    .filter(Pickup.order_id.in_(order_ids))
                    .delete(synchronize_session=False)
                )

                deleted_allocations = (
                    db.query(Allocation)
                    .filter(Allocation.order_id.in_(order_ids))
                    .delete(synchronize_session=False)
                )

                deleted_orders = (
                    db.query(Order)
                    .filter(Order.id.in_(order_ids))
                    .delete(synchronize_session=False)
                )
            else:
                deleted_allocations = (
                    db.query(Allocation)
                    .filter(Allocation.locker_id == locker_id)
                    .delete(synchronize_session=False)
                )

        db.commit()

    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail={
                "type": "DEV_LOCKER_RESET_FAILED",
                "message": "Falha ao executar reset DEV do locker.",
                "region": region,
                "locker_id": locker_id,
                "error": str(exc),
            },
        ) from exc

    return DevResetLockerOut(
        ok=True,
        region=region,
        locker_id=locker_id,
        slots_total=slots_total,
        released_allocations=released_allocations,
        slot_reset_results=slot_reset_results,
        deleted_pickups=deleted_pickups,
        deleted_allocations=deleted_allocations,
        deleted_orders=deleted_orders,
        message=(
            "Reset DEV concluído. Todas as gavetas do locker foram forçadas para AVAILABLE "
            "e os dados locais foram removidos conforme solicitado. "
            "Para conflitos órfãos do backend regional, use também /dev-admin/release-regional-allocations."
        ),
    )

# 15/04/2026
@router.post("/simulate-online-payment-legacy-not-use")
def simulate_payment(
    order_id: str,
    db: Session = Depends(get_db),
):
    _ensure_dev_mode()

    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    allocation = (
        db.query(Allocation)
        .filter(Allocation.order_id == order.id)
        .first()
    )
    if not allocation:
        raise HTTPException(status_code=404, detail="Allocation not found")

    now = datetime.now(timezone.utc)

    if str(order.payment_status or "") != "APPROVED":
        order.payment_status = "APPROVED"
        order.status = "PAID_PENDING_PICKUP"
        order.paid_at = now
        order.payment_updated_at = now

    pickup = (
        db.query(Pickup)
        .filter(Pickup.order_id == order.id)
        .order_by(Pickup.created_at.desc(), Pickup.id.desc())
        .first()
    )

    if not pickup:
        pickup = Pickup(
            id=f"pk_{uuid4().hex}",
            order_id=order.id,
            channel=PickupChannel.ONLINE,
            region=order.region,
            locker_id=allocation.locker_id or order.totem_id,
            machine_id=order.totem_id,
            slot=allocation.slot,
            status=PickupStatus.ACTIVE,
            lifecycle_stage=PickupLifecycleStage.READY_FOR_PICKUP,
            activated_at=now,
            ready_at=now,
            # pickup_window_sec=7200,  # 2h - isso existe no conceito (lógica), mas no seu sistema o correto é: expires_at
            expires_at=now + timedelta(hours=2),
            created_at=now,
            updated_at=now,
        )
        db.add(pickup)
        db.flush()
    else:
        pickup.channel = PickupChannel.ONLINE
        pickup.region = order.region
        pickup.locker_id = allocation.locker_id or order.totem_id
        pickup.machine_id = order.totem_id
        pickup.slot = allocation.slot
        pickup.status = PickupStatus.ACTIVE
        pickup.lifecycle_stage = PickupLifecycleStage.READY_FOR_PICKUP
        pickup.activated_at = pickup.activated_at or now
        pickup.ready_at = pickup.ready_at or now
        pickup.expires_at = pickup.expires_at or (now + timedelta(hours=2))
        pickup.touch()
        db.flush()

    manual_code = _generate_manual_code()
    token_hash = _sha256(manual_code)

    tok = PickupToken(
        id=str(uuid4()),
        pickup_id=pickup.id,
        token_hash=token_hash,
        expires_at=pickup.expires_at.replace(tzinfo=None),
        used_at=None,
    )
    db.add(tok)
    db.flush()

    pickup.current_token_id = tok.id
    pickup.touch()

    db.commit()
    db.refresh(order)
    db.refresh(pickup)

    return {
        "message": "Pagamento simulado + pickup/token criados",
        "order_id": order.id,
        "pickup_id": pickup.id,
        "token_id": tok.id,
        "manual_code": manual_code,
        "status": order.status,
        "payment_status": order.payment_status,
        "locker_id": pickup.locker_id,
        "slot": pickup.slot,
        "expires_at": pickup.expires_at.isoformat() if pickup.expires_at else None,
    }


# 15/04/2026 - criada e funcional - foi substituída por 17/04/2026
@router.post("/simulate-online-payment")
def simulate_payment_legacy_funcional(
    order_id: str,
    db: Session = Depends(get_db),
):
    _ensure_dev_mode()

    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    allocation = _ensure_allocation(db, order.id)

    now = datetime.now(timezone.utc)

    if str(order.payment_status or "") != "APPROVED":
        order.payment_status = "APPROVED"
        order.status = "PAID_PENDING_PICKUP"
        order.paid_at = now
        order.payment_updated_at = now

    deadline_utc = now + timedelta(hours=2)

    # pickup = _ensure_online_pickup(
    #     db,
    #     order=order,
    #     allocation=allocation,
    #     deadline_utc=deadline_utc,
    # )
    # 
    try:
        pickup = _ensure_online_pickup(
            db,
            order=order,
            allocation=allocation,
            deadline_utc=deadline_utc,
        )
    except Exception:
        try:
            backend_client.locker_release(
                order.region,
                allocation.id,
                locker_id=order.totem_id,
            )
        except Exception:
            logger.exception(
                "simulate_payment_release_after_pickup_setup_failed",
                extra={
                    "order_id": order.id,
                    "allocation_id": allocation.id,
                    "locker_id": order.totem_id,
                },
            )

        try:
            allocation.mark_released()
        except Exception:
            allocation.state = AllocationState.RELEASED

        order.status = OrderStatus.FAILED
        order.updated_at = datetime.now(timezone.utc)
        db.flush()
        db.commit()
        raise


    token_data = _create_pickup_token(
        db,
        pickup_id=pickup.id,
        expires_at_utc=deadline_utc,
    )

    pickup.current_token_id = token_data["token_id"]
    pickup.touch()

    logger.error(f"🔥 TOKEN CRIADO COM AES dev_admin - token_data={token_data}")


    db.commit()
    db.refresh(order)
    db.refresh(pickup)

    return {
        "message": "Pagamento simulado + pickup/token criados",
        "order_id": order.id,
        "pickup_id": pickup.id,
        "token_id": token_data["token_id"],
        "manual_code": token_data["manual_code"],
        "status": order.status,
        "payment_status": order.payment_status,
        "locker_id": pickup.locker_id,
        "slot": pickup.slot,
        "expires_at": pickup.expires_at.isoformat() if pickup.expires_at else None,
    }



# 17/04/2026 
@router.post("/simulate-online-payment")
def simulate_payment(
    order_id: str,
    db: Session = Depends(get_db),
):
    _ensure_dev_mode()

    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    allocation = _ensure_allocation(db, order.id)

    now = datetime.now(timezone.utc)

    # 🔥 1. Marca pagamento aprovado
    order.payment_status = "APPROVED"
    order.status = "PAID_PENDING_PICKUP"
    order.paid_at = now
    order.payment_updated_at = now

    # 🔥 2. EXECUTA PIPELINE REAL (ESSENCIAL)
    result = fulfill_payment_post_approval(
        db=db,
        order=order,
        allocation=allocation,
        pickup_window_hours=2,
    )

    pickup = result["pickup"]

    # 🔥 3. SINCRONIZA CAMPOS NA ORDER (CRÍTICO)
    order.slot = allocation.slot
    order.allocation_id = allocation.id
    order.allocation_expires_at = allocation.locked_until

    db.commit()
    db.refresh(order)
    db.refresh(pickup)

    return {
        "message": "Pagamento simulado (pipeline real executado)",
        "order_id": order.id,
        "pickup_id": pickup.id,
        "token_id": result.get("token_id"),
        "manual_code": result.get("manual_code"),
        "status": order.status,
        "payment_status": order.payment_status,
        "locker_id": pickup.locker_id,
        "slot": pickup.slot,
        "expires_at": pickup.expires_at.isoformat() if pickup.expires_at else None,
    }


