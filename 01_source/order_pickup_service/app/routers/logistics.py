from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.auth_dep import get_current_user, require_user_roles
from app.core.db import get_db
from app.models.logistics_tracking import (
    LogisticsCarrierAuthConfig,
    LogisticsCarrierStatusMap,
    LogisticsDeliveryAttempt,
    LogisticsReturn,
    LogisticsReturnEvent,
    LogisticsShipmentLabel,
    LogisticsTrackingEvent,
    ReturnLeg,
    ReturnReasonCatalog,
    ReturnRequest,
    SlaBreachEvent,
)
from app.models.logistics_manifest import LogisticsCapacityAllocation, LogisticsManifest, LogisticsManifestItem
from app.models.partner_webhook_delivery import PartnerWebhookDelivery
from app.models.partner_webhook_endpoint import PartnerWebhookEndpoint
from app.models.user import User
from app.schemas.logistics import (
    LogisticsCapacityAllocationListOut,
    LogisticsCapacityAllocationOut,
    LogisticsCapacityAllocationUpsertIn,
    LogisticsCarrierAuthConfigIn,
    LogisticsCarrierAuthConfigOut,
    LogisticsCarrierStatusMapIn,
    LogisticsCarrierStatusMapOut,
    LogisticsDeliveryAttemptListOut,
    LogisticsDeliveryAttemptOut,
    LogisticsLabelCreateIn,
    LogisticsManifestCloseIn,
    LogisticsManifestCreateIn,
    LogisticsManifestItemExceptionIn,
    LogisticsManifestItemListOut,
    LogisticsManifestItemOut,
    LogisticsManifestOpsOverviewOut,
    LogisticsManifestListOut,
    LogisticsManifestOut,
    LogisticsOpsOverviewOut,
    LogisticsReturnCreateIn,
    LogisticsReturnEventListOut,
    LogisticsReturnEventOut,
    LogisticsReturnListOut,
    LogisticsReturnOut,
    LogisticsReturnStatusUpdateIn,
    LogisticsShipmentLabelOut,
    LogisticsTrackingEventListOut,
    LogisticsTrackingEventOut,
    LogisticsWebhookEventIn,
    LogisticsWebhookIngestOut,
    ReturnReasonIn,
    ReturnReasonListOut,
    ReturnReasonOut,
    ReturnRequestCreateIn,
    ReturnRequestListOut,
    ReturnRequestOut,
    ReturnRequestStatusPatchIn,
    ReturnLegOut,
    SlaBreachEventListOut,
    SlaBreachEventOut,
)
from app.services.ops_audit_service import record_ops_action_audit

router = APIRouter(
    prefix="/logistics",
    tags=["logistics"],
    dependencies=[Depends(require_user_roles(allowed_roles={"admin_operacao", "auditoria"}))],
)

_ATTEMPT_STATUSES = {"SUCCESS", "FAILED", "RESCHEDULED", "RETURNED"}
_LABEL_FORMATS = {"PDF", "ZPL", "PNG"}
_HMAC_ALGORITHMS = {"HMAC_SHA256": "sha256"}
_RETURN_STATUSES = {"REQUESTED", "PICKUP_SCHEDULED", "IN_TRANSIT", "RECEIVED", "CLOSED"}
_RETURN_STATUS_TRANSITIONS = {
    "REQUESTED": {"PICKUP_SCHEDULED", "CLOSED"},
    "PICKUP_SCHEDULED": {"IN_TRANSIT", "CLOSED"},
    "IN_TRANSIT": {"RECEIVED", "CLOSED"},
    "RECEIVED": {"CLOSED"},
    "CLOSED": set(),
}
_RETURN_REQUESTER_TYPES = {"RECIPIENT", "SENDER", "SYSTEM", "OPS"}
_RETURN_REQUEST_STATUSES = {"REQUESTED", "APPROVED", "REJECTED", "LABEL_ISSUED", "IN_TRANSIT", "RECEIVED", "CLOSED", "DISPUTED"}


def _to_iso_utc(value: datetime | None) -> str:
    if value is None:
        return datetime.now(timezone.utc).isoformat()
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def _parse_iso_datetime_utc_optional(raw_value: str | None, *, field_name: str) -> datetime | None:
    value = str(raw_value or "").strip()
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={"type": "INVALID_DATETIME", "message": f"{field_name} inválido. Use ISO-8601."},
        ) from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _parse_iso_date_required(raw_value: str, *, field_name: str) -> date:
    value = str(raw_value or "").strip()
    if not value:
        raise HTTPException(
            status_code=422,
            detail={"type": "INVALID_DATE", "message": f"{field_name} é obrigatório no formato YYYY-MM-DD."},
        )
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={"type": "INVALID_DATE", "message": f"{field_name} inválido. Use YYYY-MM-DD."},
        ) from exc


def _parse_iso_date_optional(raw_value: str | None, *, field_name: str) -> date | None:
    value = str(raw_value or "").strip()
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={"type": "INVALID_DATE", "message": f"{field_name} inválido. Use YYYY-MM-DD."},
        ) from exc


def _json_load_dict(value: str | None) -> dict:
    try:
        parsed = json.loads(str(value or "{}"))
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass
    return {}


def _json_load_list(value: str | None, default: list[str] | None = None) -> list[str]:
    expected_default = default if default is not None else []
    try:
        parsed = json.loads(str(value or "[]"))
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
    except Exception:
        pass
    return expected_default


def _resolve_correlation_id(header_value: str | None) -> str:
    value = str(header_value or "").strip()
    return value or str(uuid4())


def _audit_ops(
    *,
    db: Session,
    action: str,
    result: str,
    correlation_id: str,
    user_id: str | None,
    error_message: str | None = None,
    details: dict | None = None,
) -> None:
    try:
        record_ops_action_audit(
            db=db,
            action=action,
            result=result,
            correlation_id=correlation_id,
            user_id=user_id,
            role="ops_user",
            error_message=error_message,
            details=details or {},
        )
    except Exception:
        pass


def _ensure_delivery_exists(db: Session, delivery_id: str) -> None:
    row = db.execute(
        text("SELECT id FROM inbound_deliveries WHERE id = :id"),
        {"id": delivery_id},
    ).mappings().first()
    if not row:
        raise HTTPException(
            status_code=404,
            detail={
                "type": "DELIVERY_NOT_FOUND",
                "message": "Entrega não encontrada para o logistics tracking.",
                "delivery_id": delivery_id,
            },
        )


def _to_tracking_out(row: LogisticsTrackingEvent) -> LogisticsTrackingEventOut:
    return LogisticsTrackingEventOut(
        id=row.id,
        delivery_id=row.delivery_id,
        event_code=row.event_code,
        event_label=row.event_label,
        raw_status=row.raw_status,
        location_city=row.location_city,
        location_state=row.location_state,
        location_country=row.location_country,
        occurred_at=_to_iso_utc(row.occurred_at),
        source=row.source,
        source_ref=row.source_ref,
        payload=_json_load_dict(row.payload_json),
        created_at=_to_iso_utc(row.created_at),
    )


def _to_attempt_out(row: LogisticsDeliveryAttempt) -> LogisticsDeliveryAttemptOut:
    return LogisticsDeliveryAttemptOut(
        id=row.id,
        delivery_id=row.delivery_id,
        attempt_number=int(row.attempt_number or 0),
        status=row.status,
        attempted_at=_to_iso_utc(row.attempted_at),
        failure_reason=row.failure_reason,
        carrier_note=row.carrier_note,
        carrier_agent=row.carrier_agent,
        proof_url=row.proof_url,
        created_at=_to_iso_utc(row.created_at),
    )


def _to_label_out(row: LogisticsShipmentLabel) -> LogisticsShipmentLabelOut:
    return LogisticsShipmentLabelOut(
        id=row.id,
        delivery_id=row.delivery_id,
        carrier_code=row.carrier_code,
        tracking_code=row.tracking_code,
        label_format=row.label_format,
        label_url=row.label_url,
        label_payload=_json_load_dict(row.label_payload),
        status=row.status,
        created_at=_to_iso_utc(row.created_at),
        expires_at=_to_iso_utc(row.expires_at) if row.expires_at else None,
    )


def _to_auth_out(row: LogisticsCarrierAuthConfig) -> LogisticsCarrierAuthConfigOut:
    return LogisticsCarrierAuthConfigOut(
        id=row.id,
        carrier_code=row.carrier_code,
        signature_header=row.signature_header,
        algorithm=row.algorithm,
        required=bool(row.required),
        active=bool(row.active),
        created_at=_to_iso_utc(row.created_at),
        updated_at=_to_iso_utc(row.updated_at),
    )


def _to_status_map_out(row: LogisticsCarrierStatusMap) -> LogisticsCarrierStatusMapOut:
    return LogisticsCarrierStatusMapOut(
        id=row.id,
        carrier_code=row.carrier_code,
        raw_status=row.raw_status,
        normalized_event_code=row.normalized_event_code,
        normalized_event_label=row.normalized_event_label,
        normalized_outcome=row.normalized_outcome,
        active=bool(row.active),
        created_at=_to_iso_utc(row.created_at),
        updated_at=_to_iso_utc(row.updated_at),
    )


def _to_return_out(row: LogisticsReturn) -> LogisticsReturnOut:
    return LogisticsReturnOut(
        id=row.id,
        order_id=row.order_id,
        partner_id=row.partner_id,
        reason_code=row.reason_code,
        status=row.status,
        notes=row.notes,
        created_by=row.created_by,
        created_at=_to_iso_utc(row.created_at),
        updated_at=_to_iso_utc(row.updated_at),
    )


def _to_return_event_out(row: LogisticsReturnEvent) -> LogisticsReturnEventOut:
    return LogisticsReturnEventOut(
        id=row.id,
        return_id=row.return_id,
        from_status=row.from_status,
        to_status=row.to_status,
        reason=row.reason,
        changed_by=row.changed_by,
        occurred_at=_to_iso_utc(row.occurred_at),
        created_at=_to_iso_utc(row.created_at),
    )


def _to_manifest_out(row: LogisticsManifest) -> LogisticsManifestOut:
    return LogisticsManifestOut(
        id=row.id,
        logistics_partner_id=row.logistics_partner_id,
        locker_id=row.locker_id,
        manifest_date=row.manifest_date.isoformat(),
        carrier_route_code=row.carrier_route_code,
        carrier_vehicle_id=row.carrier_vehicle_id,
        expected_parcel_count=int(row.expected_parcel_count or 0),
        actual_parcel_count=int(row.actual_parcel_count or 0),
        status=row.status,
        dispatched_at=_to_iso_utc(row.dispatched_at) if row.dispatched_at else None,
        delivered_at=_to_iso_utc(row.delivered_at) if row.delivered_at else None,
        carrier_note=row.carrier_note,
        created_at=_to_iso_utc(row.created_at),
        updated_at=_to_iso_utc(row.updated_at),
    )


def _to_capacity_out(row: LogisticsCapacityAllocation) -> LogisticsCapacityAllocationOut:
    return LogisticsCapacityAllocationOut(
        id=row.id,
        logistics_partner_id=row.logistics_partner_id,
        locker_id=row.locker_id,
        slot_size=row.slot_size,
        reserved_slots=int(row.reserved_slots or 0),
        valid_from=row.valid_from.isoformat(),
        valid_until=row.valid_until.isoformat() if row.valid_until else None,
        priority=int(row.priority or 100),
        notes=row.notes,
        is_active=bool(row.is_active),
        created_at=_to_iso_utc(row.created_at),
    )


def _to_manifest_item_out(row: LogisticsManifestItem) -> LogisticsManifestItemOut:
    return LogisticsManifestItemOut(
        id=int(row.id),
        manifest_id=row.manifest_id,
        delivery_id=row.delivery_id,
        tracking_code=row.tracking_code,
        sequence_number=row.sequence_number,
        status=row.status,
        exception_note=row.exception_note,
        processed_at=_to_iso_utc(row.processed_at) if row.processed_at else None,
    )


def _to_return_leg_out(row: ReturnLeg) -> ReturnLegOut:
    return ReturnLegOut(
        id=row.id,
        return_request_id=row.return_request_id,
        logistics_partner_id=row.logistics_partner_id,
        tracking_code=row.tracking_code,
        label_id=row.label_id,
        from_locker_id=row.from_locker_id,
        to_hub_address=_json_load_dict(row.to_hub_address_json),
        status=row.status,
        shipped_at=_to_iso_utc(row.shipped_at) if row.shipped_at else None,
        received_at=_to_iso_utc(row.received_at) if row.received_at else None,
        created_at=_to_iso_utc(row.created_at),
        updated_at=_to_iso_utc(row.updated_at),
    )


def _to_return_request_out(db: Session, row: ReturnRequest) -> ReturnRequestOut:
    legs = (
        db.query(ReturnLeg)
        .filter(ReturnLeg.return_request_id == row.id)
        .order_by(ReturnLeg.created_at.desc(), ReturnLeg.id.desc())
        .all()
    )
    return ReturnRequestOut(
        id=row.id,
        original_delivery_id=row.original_delivery_id,
        locker_id=row.locker_id,
        requester_type=row.requester_type,
        requester_id=row.requester_id,
        return_reason_code=row.return_reason_code,
        return_reason_detail=row.return_reason_detail,
        photo_url=row.photo_url,
        status=row.status,
        requested_at=_to_iso_utc(row.requested_at),
        approved_at=_to_iso_utc(row.approved_at) if row.approved_at else None,
        approved_by=row.approved_by,
        closed_at=_to_iso_utc(row.closed_at) if row.closed_at else None,
        close_reason=row.close_reason,
        created_at=_to_iso_utc(row.created_at),
        updated_at=_to_iso_utc(row.updated_at),
        legs=[_to_return_leg_out(item) for item in legs],
    )


def _to_return_reason_out(row: ReturnReasonCatalog) -> ReturnReasonOut:
    return ReturnReasonOut(
        id=row.id,
        code=row.code,
        label_pt=row.label_pt,
        label_en=row.label_en,
        category=row.category,
        requires_photo=bool(row.requires_photo),
        requires_detail=bool(row.requires_detail),
        is_active=bool(row.is_active),
        created_at=_to_iso_utc(row.created_at),
    )


def _to_sla_breach_out(row: SlaBreachEvent) -> SlaBreachEventOut:
    return SlaBreachEventOut(
        id=row.id,
        delivery_id=row.delivery_id,
        return_request_id=row.return_request_id,
        logistics_partner_id=row.logistics_partner_id,
        breach_type=row.breach_type,
        severity=row.severity,
        expected_at=_to_iso_utc(row.expected_at),
        detected_at=_to_iso_utc(row.detected_at),
        notified_at=_to_iso_utc(row.notified_at) if row.notified_at else None,
        resolved_at=_to_iso_utc(row.resolved_at) if row.resolved_at else None,
        notes=row.notes,
    )


def _ensure_return_reason_exists(db: Session, code: str) -> None:
    row = (
        db.query(ReturnReasonCatalog)
        .filter(
            ReturnReasonCatalog.code == str(code or "").strip().upper(),
            ReturnReasonCatalog.is_active.is_(True),
        )
        .first()
    )
    if row is None:
        raise HTTPException(
            status_code=404,
            detail={
                "type": "RETURN_REASON_NOT_FOUND",
                "message": "Motivo de devolução não encontrado/ativo.",
                "return_reason_code": str(code or "").strip().upper(),
            },
        )


def _ensure_logistics_partner_exists(db: Session, partner_id: str) -> None:
    row = db.execute(
        text("SELECT id FROM logistics_partners WHERE id = :id"),
        {"id": partner_id},
    ).mappings().first()
    if not row:
        raise HTTPException(
            status_code=404,
            detail={
                "type": "LOGISTICS_PARTNER_NOT_FOUND",
                "message": "Logistics partner não encontrado.",
                "partner_id": partner_id,
            },
        )


def _ensure_locker_exists(db: Session, locker_id: str) -> None:
    row = db.execute(
        text("SELECT id FROM lockers WHERE id = :id"),
        {"id": locker_id},
    ).mappings().first()
    if not row:
        raise HTTPException(
            status_code=404,
            detail={
                "type": "LOCKER_NOT_FOUND",
                "message": "Locker não encontrado para capacidade/manifests.",
                "locker_id": locker_id,
            },
        )


def _ensure_manifest_exists(db: Session, manifest_id: str) -> LogisticsManifest:
    row = db.get(LogisticsManifest, manifest_id)
    if row is None:
        raise HTTPException(
            status_code=404,
            detail={
                "type": "MANIFEST_NOT_FOUND",
                "message": "Manifesto não encontrado.",
                "manifest_id": manifest_id,
            },
        )
    return row


def _ensure_manifest_item_exists(
    db: Session,
    *,
    manifest_id: str,
    item_id: int,
) -> LogisticsManifestItem:
    row = (
        db.query(LogisticsManifestItem)
        .filter(
            LogisticsManifestItem.id == int(item_id),
            LogisticsManifestItem.manifest_id == manifest_id,
        )
        .first()
    )
    if row is None:
        raise HTTPException(
            status_code=404,
            detail={
                "type": "MANIFEST_ITEM_NOT_FOUND",
                "message": "Item do manifesto não encontrado.",
                "manifest_id": manifest_id,
                "item_id": item_id,
            },
        )
    return row


def _resolve_manifest_close_status(*, expected_parcel_count: int, actual_parcel_count: int) -> str:
    expected = int(expected_parcel_count or 0)
    actual = int(actual_parcel_count or 0)
    if actual <= 0:
        return "FAILED"
    if expected > 0 and actual < expected:
        return "PARTIAL"
    return "DELIVERED"


def _enqueue_return_critical_webhooks(
    *,
    db: Session,
    return_row: LogisticsReturn,
    to_status: str,
) -> int:
    normalized_status = str(to_status or "").strip().upper()
    if normalized_status not in {"RECEIVED", "CLOSED"}:
        return 0
    event_type = f"LOGISTICS_RETURN_{normalized_status}"
    now = datetime.now(timezone.utc)
    payload = {
        "return_id": return_row.id,
        "order_id": return_row.order_id,
        "partner_id": return_row.partner_id,
        "reason_code": return_row.reason_code,
        "status": return_row.status,
        "notes": return_row.notes,
        "created_at": _to_iso_utc(return_row.created_at),
        "updated_at": _to_iso_utc(return_row.updated_at),
        "event_type": event_type,
        "occurred_at": _to_iso_utc(now),
    }
    payload_json = json.dumps(payload)
    payload_hash = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()

    endpoints = (
        db.query(PartnerWebhookEndpoint)
        .filter(
            PartnerWebhookEndpoint.partner_id == return_row.partner_id,
            PartnerWebhookEndpoint.partner_type == "ECOMMERCE",
            PartnerWebhookEndpoint.active.is_(True),
        )
        .order_by(PartnerWebhookEndpoint.created_at.desc(), PartnerWebhookEndpoint.id.desc())
        .all()
    )
    enqueued = 0
    for endpoint in endpoints:
        events = {item.strip().upper() for item in _json_load_list(endpoint.events_json, ["*"]) if item}
        if "*" not in events and event_type not in events:
            continue
        db.add(
            PartnerWebhookDelivery(
                id=str(uuid4()),
                endpoint_id=endpoint.id,
                event_id=str(uuid4()),
                event_type=event_type,
                payload_json=payload_json,
                payload_hash=payload_hash,
                status="PENDING",
                attempt_count=0,
                next_retry_at=now,
                created_at=now,
            )
        )
        enqueued += 1
    return enqueued


def _with_trend(current_counter: Counter[str], previous_counter: Counter[str]) -> list[dict]:
    keys = sorted(set(current_counter.keys()) | set(previous_counter.keys()))
    rows: list[dict] = []
    for key in keys:
        current_count = int(current_counter.get(key, 0))
        previous_count = int(previous_counter.get(key, 0))
        delta = current_count - previous_count
        trend = "stable"
        if delta > 0:
            trend = "up"
        elif delta < 0:
            trend = "down"
        rows.append(
            {
                "key": key,
                "count": current_count,
                "previous_count": previous_count,
                "delta": delta,
                "trend": trend,
            }
        )
    rows.sort(key=lambda item: (-int(item["count"]), str(item["key"])))
    return rows


def _verify_carrier_hmac(
    *,
    db: Session,
    carrier_code: str,
    body_bytes: bytes,
    provided_signature: str | None,
) -> None:
    cfg = (
        db.query(LogisticsCarrierAuthConfig)
        .filter(
            LogisticsCarrierAuthConfig.carrier_code == carrier_code,
            LogisticsCarrierAuthConfig.active.is_(True),
        )
        .order_by(LogisticsCarrierAuthConfig.updated_at.desc(), LogisticsCarrierAuthConfig.id.desc())
        .first()
    )
    if not cfg:
        return
    if not cfg.required:
        return
    if not cfg.secret_key:
        raise HTTPException(
            status_code=503,
            detail={"type": "CARRIER_HMAC_NOT_CONFIGURED", "message": "Carrier exige HMAC, mas secret não está configurado."},
        )
    algorithm = str(cfg.algorithm or "").strip().upper()
    digest_name = _HMAC_ALGORITHMS.get(algorithm)
    if not digest_name:
        raise HTTPException(
            status_code=422,
            detail={"type": "UNSUPPORTED_HMAC_ALGORITHM", "message": "Algoritmo HMAC não suportado."},
        )
    signature = str(provided_signature or "").strip()
    if not signature:
        raise HTTPException(
            status_code=401,
            detail={"type": "MISSING_CARRIER_SIGNATURE", "message": f"Header de assinatura '{cfg.signature_header}' não informado."},
        )
    expected = hmac.new(cfg.secret_key.encode("utf-8"), body_bytes, getattr(hashlib, digest_name)).hexdigest()
    normalized_signature = signature.lower().replace("sha256=", "")
    if not hmac.compare_digest(expected, normalized_signature):
        raise HTTPException(
            status_code=401,
            detail={"type": "INVALID_CARRIER_SIGNATURE", "message": "Assinatura HMAC inválida para payload do carrier."},
        )


def _resolve_status_mapping(
    *,
    db: Session,
    carrier_code: str,
    raw_status: str | None,
) -> LogisticsCarrierStatusMap | None:
    status = str(raw_status or "").strip().upper()
    if not status:
        return None
    return (
        db.query(LogisticsCarrierStatusMap)
        .filter(
            LogisticsCarrierStatusMap.carrier_code == carrier_code,
            LogisticsCarrierStatusMap.raw_status == status,
            LogisticsCarrierStatusMap.active.is_(True),
        )
        .order_by(LogisticsCarrierStatusMap.updated_at.desc(), LogisticsCarrierStatusMap.id.desc())
        .first()
    )


@router.post("/ops/carriers/auth-config", response_model=LogisticsCarrierAuthConfigOut)
def upsert_logistics_carrier_auth_config(
    payload: LogisticsCarrierAuthConfigIn,
    current_user: User = Depends(get_current_user),
    correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    db: Session = Depends(get_db),
):
    corr_id = _resolve_correlation_id(correlation_id)
    carrier_code = payload.carrier_code.strip().upper()
    algorithm = payload.algorithm.strip().upper()
    if algorithm not in _HMAC_ALGORITHMS:
        raise HTTPException(status_code=422, detail={"type": "UNSUPPORTED_HMAC_ALGORITHM", "allowed": sorted(_HMAC_ALGORITHMS.keys())})

    row = (
        db.query(LogisticsCarrierAuthConfig)
        .filter(LogisticsCarrierAuthConfig.carrier_code == carrier_code)
        .first()
    )
    now = datetime.now(timezone.utc)
    if row is None:
        row = LogisticsCarrierAuthConfig(
            id=str(uuid4()),
            carrier_code=carrier_code,
            created_at=now,
            updated_at=now,
        )
        db.add(row)

    row.signature_header = payload.signature_header.strip() or "X-Carrier-Signature"
    row.algorithm = algorithm
    row.secret_key = payload.secret_key.strip() if payload.secret_key else row.secret_key
    row.required = bool(payload.required)
    row.active = bool(payload.active)
    row.updated_at = now

    _audit_ops(
        db=db,
        action="LOGISTICS_CARRIER_AUTH_CONFIG_UPSERT",
        result="SUCCESS",
        correlation_id=corr_id,
        user_id=str(current_user.id),
        details={"carrier_code": carrier_code, "required": row.required, "active": row.active, "algorithm": row.algorithm},
    )
    db.commit()
    return _to_auth_out(row)


@router.post("/ops/carriers/status-map", response_model=LogisticsCarrierStatusMapOut)
def upsert_logistics_carrier_status_map(
    payload: LogisticsCarrierStatusMapIn,
    current_user: User = Depends(get_current_user),
    correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    db: Session = Depends(get_db),
):
    corr_id = _resolve_correlation_id(correlation_id)
    carrier_code = payload.carrier_code.strip().upper()
    raw_status = payload.raw_status.strip().upper()
    normalized_outcome = payload.normalized_outcome.strip().upper() if payload.normalized_outcome else None
    if normalized_outcome and normalized_outcome not in _ATTEMPT_STATUSES:
        raise HTTPException(status_code=422, detail={"type": "INVALID_NORMALIZED_OUTCOME", "allowed_outcomes": sorted(_ATTEMPT_STATUSES)})

    row = (
        db.query(LogisticsCarrierStatusMap)
        .filter(
            LogisticsCarrierStatusMap.carrier_code == carrier_code,
            LogisticsCarrierStatusMap.raw_status == raw_status,
        )
        .first()
    )
    now = datetime.now(timezone.utc)
    if row is None:
        row = LogisticsCarrierStatusMap(
            id=str(uuid4()),
            carrier_code=carrier_code,
            raw_status=raw_status,
            created_at=now,
            updated_at=now,
        )
        db.add(row)

    row.normalized_event_code = payload.normalized_event_code.strip().upper()
    row.normalized_event_label = payload.normalized_event_label.strip()
    row.normalized_outcome = normalized_outcome
    row.active = bool(payload.active)
    row.updated_at = now

    _audit_ops(
        db=db,
        action="LOGISTICS_CARRIER_STATUS_MAP_UPSERT",
        result="SUCCESS",
        correlation_id=corr_id,
        user_id=str(current_user.id),
        details={"carrier_code": carrier_code, "raw_status": raw_status, "event_code": row.normalized_event_code, "outcome": row.normalized_outcome},
    )
    db.commit()
    return _to_status_map_out(row)


@router.post("/webhook/{carrier_code}", response_model=LogisticsWebhookIngestOut)
def post_logistics_carrier_webhook(
    carrier_code: str,
    payload: LogisticsWebhookEventIn,
    current_user: User = Depends(get_current_user),
    correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    x_carrier_signature: str | None = Header(default=None, alias="X-Carrier-Signature"),
    db: Session = Depends(get_db),
):
    corr_id = _resolve_correlation_id(correlation_id)
    normalized_carrier = str(carrier_code or "").strip().upper()
    if not normalized_carrier:
        raise HTTPException(status_code=422, detail={"type": "INVALID_CARRIER_CODE", "message": "carrier_code é obrigatório."})

    _ensure_delivery_exists(db, payload.delivery_id)
    payload_dict = payload.model_dump()
    _verify_carrier_hmac(
        db=db,
        carrier_code=normalized_carrier,
        body_bytes=json.dumps(payload_dict, separators=(",", ":"), ensure_ascii=False).encode("utf-8"),
        provided_signature=x_carrier_signature,
    )

    mapping = _resolve_status_mapping(db=db, carrier_code=normalized_carrier, raw_status=payload.raw_status)
    event_code = (mapping.normalized_event_code if mapping else (payload.event_code or "")).strip().upper()
    event_label = (mapping.normalized_event_label if mapping else (payload.event_label or "")).strip()
    if not event_code or not event_label:
        raise HTTPException(
            status_code=422,
            detail={"type": "MISSING_NORMALIZED_EVENT", "message": "Não foi possível resolver event_code/event_label. Informe no payload ou configure status-map."},
        )

    occurred_at = _parse_iso_datetime_utc_optional(payload.occurred_at, field_name="occurred_at") or datetime.now(timezone.utc)
    event_row = LogisticsTrackingEvent(
        id=str(uuid4()),
        delivery_id=payload.delivery_id.strip(),
        event_code=event_code,
        event_label=event_label,
        raw_status=(payload.raw_status.strip() if payload.raw_status else None),
        location_city=(payload.location_city.strip() if payload.location_city else None),
        location_state=(payload.location_state.strip() if payload.location_state else None),
        location_country=(payload.location_country.strip().upper() if payload.location_country else None),
        occurred_at=occurred_at,
        source=f"CARRIER_{normalized_carrier}",
        source_ref=(payload.source_ref.strip() if payload.source_ref else None),
        payload_json=json.dumps(payload.payload or {}),
        created_at=datetime.now(timezone.utc),
    )
    db.add(event_row)

    attempt_out = None
    if payload.attempt is not None or (mapping and mapping.normalized_outcome):
        default_outcome = mapping.normalized_outcome if mapping else None
        attempt_status = (
            str(payload.attempt.status or "").strip().upper()
            if payload.attempt is not None
            else str(default_outcome or "").strip().upper()
        )
        if attempt_status and attempt_status not in _ATTEMPT_STATUSES:
            raise HTTPException(status_code=422, detail={"type": "INVALID_ATTEMPT_STATUS", "allowed_statuses": sorted(_ATTEMPT_STATUSES)})
        if attempt_status:
            next_attempt_number = payload.attempt.attempt_number if payload.attempt else None
            if next_attempt_number is None:
                current_max = (
                    db.query(LogisticsDeliveryAttempt.attempt_number)
                    .filter(LogisticsDeliveryAttempt.delivery_id == payload.delivery_id)
                    .order_by(LogisticsDeliveryAttempt.attempt_number.desc())
                    .first()
                )
                next_attempt_number = int(current_max[0]) + 1 if current_max else 1

            attempt_row = LogisticsDeliveryAttempt(
                id=str(uuid4()),
                delivery_id=payload.delivery_id.strip(),
                attempt_number=int(next_attempt_number),
                status=attempt_status,
                attempted_at=(
                    _parse_iso_datetime_utc_optional(payload.attempt.attempted_at if payload.attempt else None, field_name="attempt.attempted_at")
                    or occurred_at
                ),
                failure_reason=(payload.attempt.failure_reason.strip() if payload.attempt and payload.attempt.failure_reason else None),
                carrier_note=(payload.attempt.carrier_note.strip() if payload.attempt and payload.attempt.carrier_note else None),
                carrier_agent=(payload.attempt.carrier_agent.strip() if payload.attempt and payload.attempt.carrier_agent else None),
                proof_url=(payload.attempt.proof_url.strip() if payload.attempt and payload.attempt.proof_url else None),
                created_at=datetime.now(timezone.utc),
            )
            db.add(attempt_row)
            attempt_out = attempt_row

    _audit_ops(
        db=db,
        action="LOGISTICS_CARRIER_WEBHOOK_INGEST",
        result="SUCCESS",
        correlation_id=corr_id,
        user_id=str(current_user.id),
        details={
            "carrier_code": normalized_carrier,
            "delivery_id": payload.delivery_id,
            "event_code": event_row.event_code,
            "raw_status": payload.raw_status,
            "attempt_status": attempt_out.status if attempt_out else None,
        },
    )
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail={"type": "LOGISTICS_EVENT_CONFLICT", "message": "Conflito ao registrar evento/tentativa."}) from exc

    return LogisticsWebhookIngestOut(ok=True, carrier_code=normalized_carrier, event=_to_tracking_out(event_row), attempt=_to_attempt_out(attempt_out) if attempt_out else None)


@router.get("/deliveries/{delivery_id}/tracking", response_model=LogisticsTrackingEventListOut)
def get_logistics_delivery_tracking(delivery_id: str, limit: int = Query(default=200, ge=1, le=1000), db: Session = Depends(get_db)):
    _ensure_delivery_exists(db, delivery_id)
    rows = (
        db.query(LogisticsTrackingEvent)
        .filter(LogisticsTrackingEvent.delivery_id == delivery_id)
        .order_by(LogisticsTrackingEvent.occurred_at.desc(), LogisticsTrackingEvent.id.desc())
        .limit(limit)
        .all()
    )
    return LogisticsTrackingEventListOut(ok=True, total=len(rows), items=[_to_tracking_out(row) for row in rows])


@router.get("/deliveries/{delivery_id}/attempts", response_model=LogisticsDeliveryAttemptListOut)
def get_logistics_delivery_attempts(delivery_id: str, limit: int = Query(default=200, ge=1, le=1000), db: Session = Depends(get_db)):
    _ensure_delivery_exists(db, delivery_id)
    rows = (
        db.query(LogisticsDeliveryAttempt)
        .filter(LogisticsDeliveryAttempt.delivery_id == delivery_id)
        .order_by(LogisticsDeliveryAttempt.attempt_number.desc(), LogisticsDeliveryAttempt.id.desc())
        .limit(limit)
        .all()
    )
    return LogisticsDeliveryAttemptListOut(ok=True, total=len(rows), items=[_to_attempt_out(row) for row in rows])


@router.post("/deliveries/{delivery_id}/labels", response_model=LogisticsShipmentLabelOut)
def post_logistics_delivery_label(
    delivery_id: str,
    payload: LogisticsLabelCreateIn,
    current_user: User = Depends(get_current_user),
    correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    db: Session = Depends(get_db),
):
    corr_id = _resolve_correlation_id(correlation_id)
    _ensure_delivery_exists(db, delivery_id)
    carrier_code = str(payload.carrier_code or "").strip().upper()
    if not carrier_code:
        raise HTTPException(status_code=422, detail={"type": "INVALID_CARRIER_CODE", "message": "carrier_code é obrigatório."})
    label_format = str(payload.label_format or "PDF").strip().upper()
    if label_format not in _LABEL_FORMATS:
        raise HTTPException(status_code=422, detail={"type": "INVALID_LABEL_FORMAT", "allowed_formats": sorted(_LABEL_FORMATS)})
    tracking_code = (payload.tracking_code.strip() if payload.tracking_code else "") or f"{carrier_code}-{secrets.token_hex(8).upper()}"
    row = LogisticsShipmentLabel(
        id=str(uuid4()),
        delivery_id=delivery_id,
        carrier_code=carrier_code,
        tracking_code=tracking_code,
        label_format=label_format,
        label_url=(payload.label_url.strip() if payload.label_url else None),
        label_payload=json.dumps(payload.label_payload or {}),
        status="GENERATED",
        created_at=datetime.now(timezone.utc),
        expires_at=_parse_iso_datetime_utc_optional(payload.expires_at, field_name="expires_at"),
    )
    db.add(row)
    _audit_ops(
        db=db,
        action="LOGISTICS_LABEL_CREATE",
        result="SUCCESS",
        correlation_id=corr_id,
        user_id=str(current_user.id),
        details={"delivery_id": delivery_id, "carrier_code": carrier_code, "label_id": row.id, "tracking_code": tracking_code, "label_format": label_format},
    )
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail={"type": "TRACKING_CODE_CONFLICT", "message": "tracking_code já existe."}) from exc
    return _to_label_out(row)


@router.get("/deliveries/{delivery_id}/labels/{label_id}", response_model=LogisticsShipmentLabelOut)
def get_logistics_delivery_label(delivery_id: str, label_id: str, db: Session = Depends(get_db)):
    _ensure_delivery_exists(db, delivery_id)
    row = db.get(LogisticsShipmentLabel, label_id)
    if not row or row.delivery_id != delivery_id:
        raise HTTPException(status_code=404, detail={"type": "LABEL_NOT_FOUND", "message": "Label não encontrada para esta entrega."})
    return _to_label_out(row)


@router.post("/manifests", response_model=LogisticsManifestOut)
def post_logistics_manifest(
    payload: LogisticsManifestCreateIn,
    current_user: User = Depends(get_current_user),
    correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    db: Session = Depends(get_db),
):
    corr_id = _resolve_correlation_id(correlation_id)
    partner_id = payload.logistics_partner_id.strip()
    locker_id = payload.locker_id.strip()
    if not partner_id or not locker_id:
        raise HTTPException(
            status_code=422,
            detail={"type": "INVALID_MANIFEST_PAYLOAD", "message": "logistics_partner_id e locker_id são obrigatórios."},
        )
    _ensure_logistics_partner_exists(db, partner_id)
    _ensure_locker_exists(db, locker_id)

    manifest_date = _parse_iso_date_required(payload.manifest_date, field_name="manifest_date")
    now = datetime.now(timezone.utc)
    row = LogisticsManifest(
        id=str(uuid4()),
        logistics_partner_id=partner_id,
        locker_id=locker_id,
        manifest_date=manifest_date,
        carrier_route_code=payload.carrier_route_code.strip() if payload.carrier_route_code else None,
        carrier_vehicle_id=payload.carrier_vehicle_id.strip() if payload.carrier_vehicle_id else None,
        expected_parcel_count=int(payload.expected_parcel_count),
        actual_parcel_count=0,
        status="PENDING",
        carrier_note=payload.carrier_note.strip() if payload.carrier_note else None,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    after = {
        "id": row.id,
        "logistics_partner_id": row.logistics_partner_id,
        "locker_id": row.locker_id,
        "manifest_date": row.manifest_date.isoformat(),
        "status": row.status,
        "expected_parcel_count": row.expected_parcel_count,
        "actual_parcel_count": row.actual_parcel_count,
    }
    _audit_ops(
        db=db,
        action="L3_MANIFEST_CREATE",
        result="SUCCESS",
        correlation_id=corr_id,
        user_id=str(current_user.id),
        details={"before": None, "after": after},
    )
    db.commit()
    return _to_manifest_out(row)


@router.post("/{partner_id}/capacity", response_model=LogisticsCapacityAllocationOut)
def post_logistics_capacity_allocation(
    partner_id: str,
    payload: LogisticsCapacityAllocationUpsertIn,
    current_user: User = Depends(get_current_user),
    correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    db: Session = Depends(get_db),
):
    corr_id = _resolve_correlation_id(correlation_id)
    normalized_partner_id = str(partner_id or "").strip()
    if not normalized_partner_id:
        raise HTTPException(status_code=422, detail={"type": "INVALID_PARTNER_ID", "message": "partner_id é obrigatório."})
    _ensure_logistics_partner_exists(db, normalized_partner_id)

    slot_size = str(payload.slot_size or "").strip().upper()
    if slot_size not in {"S", "M", "L", "XL"}:
        raise HTTPException(status_code=422, detail={"type": "INVALID_SLOT_SIZE", "allowed_slot_sizes": ["L", "M", "S", "XL"]})
    locker_id = str(payload.locker_id).strip()
    _ensure_locker_exists(db, locker_id)
    valid_from = _parse_iso_date_required(payload.valid_from, field_name="valid_from")
    valid_until = _parse_iso_date_optional(payload.valid_until, field_name="valid_until")
    if valid_until is not None and valid_until < valid_from:
        raise HTTPException(
            status_code=422,
            detail={"type": "INVALID_DATE_RANGE", "message": "valid_until deve ser >= valid_from."},
        )

    row = (
        db.query(LogisticsCapacityAllocation)
        .filter(
            LogisticsCapacityAllocation.logistics_partner_id == normalized_partner_id,
            LogisticsCapacityAllocation.locker_id == locker_id,
            LogisticsCapacityAllocation.slot_size == slot_size,
            LogisticsCapacityAllocation.valid_from == valid_from,
        )
        .order_by(LogisticsCapacityAllocation.created_at.desc(), LogisticsCapacityAllocation.id.desc())
        .first()
    )

    before = None
    if row is None:
        row = LogisticsCapacityAllocation(
            id=str(uuid4()),
            logistics_partner_id=normalized_partner_id,
            locker_id=locker_id,
            slot_size=slot_size,
            reserved_slots=int(payload.reserved_slots),
            valid_from=valid_from,
            valid_until=valid_until,
            priority=int(payload.priority),
            notes=payload.notes.strip() if payload.notes else None,
            is_active=bool(payload.is_active),
            created_at=datetime.now(timezone.utc),
        )
        db.add(row)
        action = "L3_CAPACITY_CREATE"
    else:
        before = {
            "id": row.id,
            "logistics_partner_id": row.logistics_partner_id,
            "locker_id": row.locker_id,
            "slot_size": row.slot_size,
            "reserved_slots": int(row.reserved_slots or 0),
            "valid_from": row.valid_from.isoformat(),
            "valid_until": row.valid_until.isoformat() if row.valid_until else None,
            "priority": int(row.priority or 100),
            "notes": row.notes,
            "is_active": bool(row.is_active),
        }
        row.reserved_slots = int(payload.reserved_slots)
        row.valid_until = valid_until
        row.priority = int(payload.priority)
        row.notes = payload.notes.strip() if payload.notes else None
        row.is_active = bool(payload.is_active)
        action = "L3_CAPACITY_UPDATE"

    after = {
        "id": row.id,
        "logistics_partner_id": row.logistics_partner_id,
        "locker_id": row.locker_id,
        "slot_size": row.slot_size,
        "reserved_slots": int(row.reserved_slots or 0),
        "valid_from": row.valid_from.isoformat(),
        "valid_until": row.valid_until.isoformat() if row.valid_until else None,
        "priority": int(row.priority or 100),
        "notes": row.notes,
        "is_active": bool(row.is_active),
    }
    _audit_ops(
        db=db,
        action=action,
        result="SUCCESS",
        correlation_id=corr_id,
        user_id=str(current_user.id),
        details={"partner_id": normalized_partner_id, "before": before, "after": after},
    )
    db.commit()
    return _to_capacity_out(row)


@router.get("/manifests", response_model=LogisticsManifestListOut)
def list_logistics_manifests(
    logistics_partner_id: str | None = Query(default=None),
    locker_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    manifest_date_from: str | None = Query(default=None),
    manifest_date_to: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(LogisticsManifest)
    normalized_partner = str(logistics_partner_id or "").strip()
    normalized_locker = str(locker_id or "").strip()
    normalized_status = str(status or "").strip().upper()
    allowed_statuses = {"PENDING", "IN_TRANSIT", "DELIVERED", "PARTIAL", "FAILED", "CANCELLED"}

    if normalized_partner:
        query = query.filter(LogisticsManifest.logistics_partner_id == normalized_partner)
    if normalized_locker:
        query = query.filter(LogisticsManifest.locker_id == normalized_locker)
    if normalized_status:
        if normalized_status not in allowed_statuses:
            raise HTTPException(status_code=422, detail={"type": "INVALID_MANIFEST_STATUS", "allowed_statuses": sorted(allowed_statuses)})
        query = query.filter(LogisticsManifest.status == normalized_status)

    from_date = _parse_iso_date_optional(manifest_date_from, field_name="manifest_date_from")
    to_date = _parse_iso_date_optional(manifest_date_to, field_name="manifest_date_to")
    if from_date and to_date and from_date > to_date:
        raise HTTPException(status_code=422, detail={"type": "INVALID_DATE_RANGE", "message": "manifest_date_from deve ser <= manifest_date_to."})
    if from_date:
        query = query.filter(LogisticsManifest.manifest_date >= from_date)
    if to_date:
        query = query.filter(LogisticsManifest.manifest_date <= to_date)

    total = query.count()
    rows = (
        query.order_by(LogisticsManifest.manifest_date.desc(), LogisticsManifest.created_at.desc(), LogisticsManifest.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return LogisticsManifestListOut(ok=True, total=total, items=[_to_manifest_out(row) for row in rows])


@router.get("/manifests/{manifest_id}/items", response_model=LogisticsManifestItemListOut)
def list_logistics_manifest_items(
    manifest_id: str,
    status: str | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    manifest = _ensure_manifest_exists(db, manifest_id)
    query = db.query(LogisticsManifestItem).filter(LogisticsManifestItem.manifest_id == manifest.id)
    normalized_status = str(status or "").strip().upper()
    allowed_statuses = {"EXPECTED", "STORED", "EXCEPTION", "MISSING"}
    if normalized_status:
        if normalized_status not in allowed_statuses:
            raise HTTPException(status_code=422, detail={"type": "INVALID_MANIFEST_ITEM_STATUS", "allowed_statuses": sorted(allowed_statuses)})
        query = query.filter(LogisticsManifestItem.status == normalized_status)
    total = query.count()
    rows = (
        query.order_by(LogisticsManifestItem.sequence_number.asc(), LogisticsManifestItem.id.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return LogisticsManifestItemListOut(ok=True, total=total, items=[_to_manifest_item_out(row) for row in rows])


@router.post("/manifests/{manifest_id}/close", response_model=LogisticsManifestOut)
def close_logistics_manifest(
    manifest_id: str,
    payload: LogisticsManifestCloseIn,
    current_user: User = Depends(get_current_user),
    correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    db: Session = Depends(get_db),
):
    corr_id = _resolve_correlation_id(correlation_id)
    manifest = _ensure_manifest_exists(db, manifest_id)
    if manifest.status == "CANCELLED":
        raise HTTPException(
            status_code=409,
            detail={
                "type": "MANIFEST_CANCELLED_NOT_CLOSABLE",
                "message": "Manifesto cancelado não pode ser fechado.",
                "manifest_id": manifest_id,
            },
        )

    before = {
        "id": manifest.id,
        "status": manifest.status,
        "expected_parcel_count": int(manifest.expected_parcel_count or 0),
        "actual_parcel_count": int(manifest.actual_parcel_count or 0),
        "delivered_at": _to_iso_utc(manifest.delivered_at) if manifest.delivered_at else None,
        "carrier_note": manifest.carrier_note,
    }

    if manifest.status in {"DELIVERED", "PARTIAL", "FAILED"}:
        after = {
            "id": manifest.id,
            "status": manifest.status,
            "expected_parcel_count": int(manifest.expected_parcel_count or 0),
            "actual_parcel_count": int(manifest.actual_parcel_count or 0),
            "delivered_at": _to_iso_utc(manifest.delivered_at) if manifest.delivered_at else None,
            "carrier_note": manifest.carrier_note,
        }
        _audit_ops(
            db=db,
            action="L3_MANIFEST_CLOSE",
            result="SUCCESS",
            correlation_id=corr_id,
            user_id=str(current_user.id),
            details={
                "manifest_id": manifest.id,
                "idempotent": True,
                "before": before,
                "after": after,
            },
        )
        db.commit()
        return _to_manifest_out(manifest)

    now = datetime.now(timezone.utc)
    stored_count = (
        db.query(LogisticsManifestItem)
        .filter(
            LogisticsManifestItem.manifest_id == manifest.id,
            LogisticsManifestItem.status == "STORED",
        )
        .count()
    )
    processed_count = (
        db.query(LogisticsManifestItem)
        .filter(
            LogisticsManifestItem.manifest_id == manifest.id,
            LogisticsManifestItem.status.in_(["STORED", "EXCEPTION", "MISSING"]),
        )
        .count()
    )
    actual_count = int(payload.actual_parcel_count) if payload.actual_parcel_count is not None else int(processed_count)
    resolved_status = _resolve_manifest_close_status(
        expected_parcel_count=int(manifest.expected_parcel_count or 0),
        actual_parcel_count=actual_count,
    )

    manifest.actual_parcel_count = actual_count
    manifest.status = resolved_status
    manifest.delivered_at = now
    manifest.updated_at = now
    if payload.carrier_note is not None:
        manifest.carrier_note = payload.carrier_note.strip() or None

    after = {
        "id": manifest.id,
        "status": manifest.status,
        "expected_parcel_count": int(manifest.expected_parcel_count or 0),
        "actual_parcel_count": int(manifest.actual_parcel_count or 0),
        "delivered_at": _to_iso_utc(manifest.delivered_at) if manifest.delivered_at else None,
        "carrier_note": manifest.carrier_note,
    }
    _audit_ops(
        db=db,
        action="L3_MANIFEST_CLOSE",
        result="SUCCESS",
        correlation_id=corr_id,
        user_id=str(current_user.id),
        details={
            "manifest_id": manifest.id,
            "idempotent": False,
            "before": before,
            "after": after,
            "reconciliation": {
                "expected_parcel_count": int(manifest.expected_parcel_count or 0),
                "actual_parcel_count": actual_count,
                "stored_count": int(stored_count),
                "processed_count": int(processed_count),
                "resolved_status": resolved_status,
            },
        },
    )
    db.commit()
    return _to_manifest_out(manifest)


@router.post("/manifests/{manifest_id}/items/{item_id}/exception", response_model=LogisticsManifestItemOut)
def mark_logistics_manifest_item_exception(
    manifest_id: str,
    item_id: int,
    payload: LogisticsManifestItemExceptionIn,
    current_user: User = Depends(get_current_user),
    correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    db: Session = Depends(get_db),
):
    corr_id = _resolve_correlation_id(correlation_id)
    _ensure_manifest_exists(db, manifest_id)
    item = _ensure_manifest_item_exists(db, manifest_id=manifest_id, item_id=item_id)

    reason = payload.reason.strip()
    before = {
        "id": int(item.id),
        "manifest_id": item.manifest_id,
        "status": item.status,
        "exception_note": item.exception_note,
        "processed_at": _to_iso_utc(item.processed_at) if item.processed_at else None,
    }

    if str(item.status or "").strip().upper() == "EXCEPTION":
        after = {
            "id": int(item.id),
            "manifest_id": item.manifest_id,
            "status": item.status,
            "exception_note": item.exception_note,
            "processed_at": _to_iso_utc(item.processed_at) if item.processed_at else None,
        }
        _audit_ops(
            db=db,
            action="L3_MANIFEST_ITEM_EXCEPTION",
            result="SUCCESS",
            correlation_id=corr_id,
            user_id=str(current_user.id),
            details={
                "manifest_id": manifest_id,
                "item_id": int(item.id),
                "idempotent": True,
                "requested_reason": reason,
                "before": before,
                "after": after,
            },
        )
        db.commit()
        return _to_manifest_item_out(item)

    now = datetime.now(timezone.utc)
    item.status = "EXCEPTION"
    item.exception_note = reason
    item.processed_at = now

    after = {
        "id": int(item.id),
        "manifest_id": item.manifest_id,
        "status": item.status,
        "exception_note": item.exception_note,
        "processed_at": _to_iso_utc(item.processed_at) if item.processed_at else None,
    }
    _audit_ops(
        db=db,
        action="L3_MANIFEST_ITEM_EXCEPTION",
        result="SUCCESS",
        correlation_id=corr_id,
        user_id=str(current_user.id),
        details={
            "manifest_id": manifest_id,
            "item_id": int(item.id),
            "idempotent": False,
            "before": before,
            "after": after,
        },
    )
    db.commit()
    return _to_manifest_item_out(item)


@router.get("/{partner_id}/capacity", response_model=LogisticsCapacityAllocationListOut)
def list_logistics_capacity_allocations(
    partner_id: str,
    locker_id: str | None = Query(default=None),
    slot_size: str | None = Query(default=None),
    active_only: bool = Query(default=True),
    valid_on: str | None = Query(default=None, description="YYYY-MM-DD"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    normalized_partner = str(partner_id or "").strip()
    if not normalized_partner:
        raise HTTPException(status_code=422, detail={"type": "INVALID_PARTNER_ID", "message": "partner_id é obrigatório."})
    _ensure_logistics_partner_exists(db, normalized_partner)

    query = db.query(LogisticsCapacityAllocation).filter(LogisticsCapacityAllocation.logistics_partner_id == normalized_partner)
    normalized_locker = str(locker_id or "").strip()
    if normalized_locker:
        query = query.filter(LogisticsCapacityAllocation.locker_id == normalized_locker)

    normalized_slot_size = str(slot_size or "").strip().upper()
    if normalized_slot_size:
        if normalized_slot_size not in {"S", "M", "L", "XL"}:
            raise HTTPException(status_code=422, detail={"type": "INVALID_SLOT_SIZE", "allowed_slot_sizes": ["L", "M", "S", "XL"]})
        query = query.filter(LogisticsCapacityAllocation.slot_size == normalized_slot_size)

    if active_only:
        query = query.filter(LogisticsCapacityAllocation.is_active.is_(True))

    valid_on_date = _parse_iso_date_optional(valid_on, field_name="valid_on")
    if valid_on_date:
        query = query.filter(LogisticsCapacityAllocation.valid_from <= valid_on_date)
        query = query.filter(
            (LogisticsCapacityAllocation.valid_until.is_(None))
            | (LogisticsCapacityAllocation.valid_until >= valid_on_date)
        )

    total = query.count()
    rows = (
        query.order_by(
            LogisticsCapacityAllocation.priority.asc(),
            LogisticsCapacityAllocation.valid_from.desc(),
            LogisticsCapacityAllocation.created_at.desc(),
            LogisticsCapacityAllocation.id.desc(),
        )
        .offset(offset)
        .limit(limit)
        .all()
    )
    return LogisticsCapacityAllocationListOut(ok=True, total=total, items=[_to_capacity_out(row) for row in rows])


@router.post("/deliveries/{delivery_id}/return-request", response_model=ReturnRequestOut)
def post_delivery_return_request(
    delivery_id: str,
    payload: ReturnRequestCreateIn,
    current_user: User = Depends(get_current_user),
    correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    db: Session = Depends(get_db),
):
    corr_id = _resolve_correlation_id(correlation_id)
    _ensure_delivery_exists(db, delivery_id)
    requester_type = str(payload.requester_type or "").strip().upper()
    if requester_type not in _RETURN_REQUESTER_TYPES:
        raise HTTPException(status_code=422, detail={"type": "INVALID_REQUESTER_TYPE", "allowed_requester_types": sorted(_RETURN_REQUESTER_TYPES)})
    reason_code = str(payload.return_reason_code or "").strip().upper()
    _ensure_return_reason_exists(db, reason_code)

    delivery_ref = db.execute(
        text("SELECT locker_id FROM inbound_deliveries WHERE id = :id"),
        {"id": delivery_id},
    ).mappings().first() or {}
    locker_id = str(delivery_ref.get("locker_id") or "").strip() or None

    now = datetime.now(timezone.utc)
    row = ReturnRequest(
        id=str(uuid4()),
        original_delivery_id=delivery_id,
        locker_id=locker_id,
        requester_type=requester_type,
        requester_id=(payload.requester_id.strip() if payload.requester_id else None),
        return_reason_code=reason_code,
        return_reason_detail=(payload.return_reason_detail.strip() if payload.return_reason_detail else None),
        photo_url=(payload.photo_url.strip() if payload.photo_url else None),
        status="REQUESTED",
        requested_at=now,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    _audit_ops(
        db=db,
        action="L2_RETURN_REQUEST_CREATE",
        result="SUCCESS",
        correlation_id=corr_id,
        user_id=str(current_user.id),
        details={
            "before": None,
            "after": {
                "id": row.id,
                "original_delivery_id": row.original_delivery_id,
                "requester_type": row.requester_type,
                "return_reason_code": row.return_reason_code,
                "status": row.status,
            },
        },
    )
    db.commit()
    return _to_return_request_out(db, row)


@router.get("/return-requests/{return_request_id}", response_model=ReturnRequestOut)
def get_return_request(return_request_id: str, db: Session = Depends(get_db)):
    row = db.get(ReturnRequest, return_request_id)
    if row is None:
        raise HTTPException(status_code=404, detail={"type": "RETURN_REQUEST_NOT_FOUND", "message": "Solicitação de devolução não encontrada."})
    return _to_return_request_out(db, row)


@router.get("/return-requests", response_model=ReturnRequestListOut)
def list_return_requests(
    status: str | None = Query(default=None),
    requester_type: str | None = Query(default=None),
    return_reason_code: str | None = Query(default=None),
    original_delivery_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=300),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(ReturnRequest)
    normalized_status = str(status or "").strip().upper()
    if normalized_status:
        if normalized_status not in _RETURN_REQUEST_STATUSES:
            raise HTTPException(status_code=422, detail={"type": "INVALID_RETURN_REQUEST_STATUS", "allowed_statuses": sorted(_RETURN_REQUEST_STATUSES)})
        query = query.filter(ReturnRequest.status == normalized_status)

    normalized_requester_type = str(requester_type or "").strip().upper()
    if normalized_requester_type:
        if normalized_requester_type not in _RETURN_REQUESTER_TYPES:
            raise HTTPException(status_code=422, detail={"type": "INVALID_REQUESTER_TYPE", "allowed_requester_types": sorted(_RETURN_REQUESTER_TYPES)})
        query = query.filter(ReturnRequest.requester_type == normalized_requester_type)

    normalized_reason_code = str(return_reason_code or "").strip().upper()
    if normalized_reason_code:
        query = query.filter(ReturnRequest.return_reason_code == normalized_reason_code)

    normalized_delivery_id = str(original_delivery_id or "").strip()
    if normalized_delivery_id:
        query = query.filter(ReturnRequest.original_delivery_id == normalized_delivery_id)

    total = query.count()
    rows = (
        query.order_by(ReturnRequest.requested_at.desc(), ReturnRequest.created_at.desc(), ReturnRequest.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return ReturnRequestListOut(ok=True, total=total, items=[_to_return_request_out(db, row) for row in rows])


@router.patch("/return-requests/{return_request_id}/status", response_model=ReturnRequestOut)
def patch_return_request_status(
    return_request_id: str,
    payload: ReturnRequestStatusPatchIn,
    current_user: User = Depends(get_current_user),
    correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    db: Session = Depends(get_db),
):
    corr_id = _resolve_correlation_id(correlation_id)
    row = db.get(ReturnRequest, return_request_id)
    if row is None:
        raise HTTPException(status_code=404, detail={"type": "RETURN_REQUEST_NOT_FOUND", "message": "Solicitação de devolução não encontrada."})

    next_status = str(payload.status or "").strip().upper()
    if next_status not in _RETURN_REQUEST_STATUSES:
        raise HTTPException(status_code=422, detail={"type": "INVALID_RETURN_REQUEST_STATUS", "allowed_statuses": sorted(_RETURN_REQUEST_STATUSES)})
    before = {
        "id": row.id,
        "status": row.status,
        "approved_at": _to_iso_utc(row.approved_at) if row.approved_at else None,
        "closed_at": _to_iso_utc(row.closed_at) if row.closed_at else None,
        "close_reason": row.close_reason,
    }
    now = datetime.now(timezone.utc)
    row.status = next_status
    row.updated_at = now
    if next_status == "APPROVED" and row.approved_at is None:
        row.approved_at = now
        row.approved_by = str(current_user.id)
    if next_status == "CLOSED":
        row.closed_at = now
        row.close_reason = (payload.close_reason.strip() if payload.close_reason else row.close_reason)

    _audit_ops(
        db=db,
        action="L2_RETURN_REQUEST_STATUS_PATCH",
        result="SUCCESS",
        correlation_id=corr_id,
        user_id=str(current_user.id),
        details={
            "before": before,
            "after": {
                "id": row.id,
                "status": row.status,
                "approved_at": _to_iso_utc(row.approved_at) if row.approved_at else None,
                "closed_at": _to_iso_utc(row.closed_at) if row.closed_at else None,
                "close_reason": row.close_reason,
            },
        },
    )
    db.commit()
    return _to_return_request_out(db, row)


@router.post("/return-requests/{return_request_id}/labels", response_model=ReturnLegOut)
def post_return_request_label(
    return_request_id: str,
    current_user: User = Depends(get_current_user),
    correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    db: Session = Depends(get_db),
):
    corr_id = _resolve_correlation_id(correlation_id)
    row = db.get(ReturnRequest, return_request_id)
    if row is None:
        raise HTTPException(status_code=404, detail={"type": "RETURN_REQUEST_NOT_FOUND", "message": "Solicitação de devolução não encontrada."})

    existing_leg = (
        db.query(ReturnLeg)
        .filter(ReturnLeg.return_request_id == return_request_id)
        .order_by(ReturnLeg.created_at.desc(), ReturnLeg.id.desc())
        .first()
    )
    if existing_leg:
        return _to_return_leg_out(existing_leg)

    now = datetime.now(timezone.utc)
    leg = ReturnLeg(
        id=str(uuid4()),
        return_request_id=return_request_id,
        logistics_partner_id=None,
        tracking_code=f"RET-{secrets.token_hex(6).upper()}",
        label_id=None,
        from_locker_id=row.locker_id,
        to_hub_address_json=json.dumps({}),
        status="PENDING",
        created_at=now,
        updated_at=now,
    )
    db.add(leg)
    row.status = "LABEL_ISSUED"
    row.updated_at = now
    _audit_ops(
        db=db,
        action="L2_RETURN_LABEL_CREATE",
        result="SUCCESS",
        correlation_id=corr_id,
        user_id=str(current_user.id),
        details={"return_request_id": return_request_id, "return_leg_id": leg.id, "tracking_code": leg.tracking_code},
    )
    db.commit()
    return _to_return_leg_out(leg)


@router.get("/sla-breaches", response_model=SlaBreachEventListOut)
def list_sla_breaches(
    logistics_partner_id: str | None = Query(default=None),
    breach_type: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    resolved: bool | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    query = db.query(SlaBreachEvent)
    if logistics_partner_id:
        query = query.filter(SlaBreachEvent.logistics_partner_id == str(logistics_partner_id).strip())
    if breach_type:
        query = query.filter(SlaBreachEvent.breach_type == str(breach_type).strip().upper())
    if severity:
        query = query.filter(SlaBreachEvent.severity == str(severity).strip().upper())
    if resolved is True:
        query = query.filter(SlaBreachEvent.resolved_at.is_not(None))
    elif resolved is False:
        query = query.filter(SlaBreachEvent.resolved_at.is_(None))
    rows = (
        query.order_by(SlaBreachEvent.detected_at.desc(), SlaBreachEvent.id.desc())
        .limit(limit)
        .all()
    )
    return SlaBreachEventListOut(ok=True, total=len(rows), items=[_to_sla_breach_out(row) for row in rows])


@router.get("/return-reasons", response_model=ReturnReasonListOut)
def list_return_reasons(
    only_active: bool = Query(default=True),
    limit: int = Query(default=200, ge=1, le=500),
    db: Session = Depends(get_db),
):
    query = db.query(ReturnReasonCatalog)
    if only_active:
        query = query.filter(ReturnReasonCatalog.is_active.is_(True))
    rows = (
        query.order_by(ReturnReasonCatalog.created_at.desc(), ReturnReasonCatalog.id.desc())
        .limit(limit)
        .all()
    )
    return ReturnReasonListOut(ok=True, total=len(rows), items=[_to_return_reason_out(row) for row in rows])


@router.post("/return-reasons", response_model=ReturnReasonOut)
def post_return_reason(
    payload: ReturnReasonIn,
    current_user: User = Depends(get_current_user),
    correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    db: Session = Depends(get_db),
):
    corr_id = _resolve_correlation_id(correlation_id)
    code = str(payload.code or "").strip().upper()
    if not code:
        raise HTTPException(status_code=422, detail={"type": "INVALID_RETURN_REASON_CODE", "message": "code é obrigatório."})

    row = (
        db.query(ReturnReasonCatalog)
        .filter(ReturnReasonCatalog.code == code)
        .first()
    )
    now = datetime.now(timezone.utc)
    before = None
    if row is None:
        row = ReturnReasonCatalog(
            id=str(uuid4()),
            code=code,
            created_at=now,
        )
        db.add(row)
    else:
        before = _to_return_reason_out(row).model_dump()
    row.label_pt = payload.label_pt.strip()
    row.label_en = payload.label_en.strip() if payload.label_en else None
    row.category = payload.category.strip().upper() if payload.category else None
    row.requires_photo = bool(payload.requires_photo)
    row.requires_detail = bool(payload.requires_detail)
    row.is_active = bool(payload.is_active)
    _audit_ops(
        db=db,
        action="L2_RETURN_REASON_UPSERT",
        result="SUCCESS",
        correlation_id=corr_id,
        user_id=str(current_user.id),
        details={"before": before, "after": _to_return_reason_out(row).model_dump()},
    )
    db.commit()
    return _to_return_reason_out(row)


@router.post("/returns", response_model=LogisticsReturnOut)
def post_logistics_return(
    payload: LogisticsReturnCreateIn,
    current_user: User = Depends(get_current_user),
    correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    db: Session = Depends(get_db),
):
    corr_id = _resolve_correlation_id(correlation_id)
    order_id = payload.order_id.strip()
    partner_id = payload.partner_id.strip()
    reason_code = payload.reason_code.strip().upper()
    if not order_id or not partner_id or not reason_code:
        raise HTTPException(
            status_code=422,
            detail={"type": "INVALID_RETURN_PAYLOAD", "message": "order_id, partner_id e reason_code são obrigatórios."},
        )
    now = datetime.now(timezone.utc)
    row = LogisticsReturn(
        id=str(uuid4()),
        order_id=order_id,
        partner_id=partner_id,
        reason_code=reason_code,
        status="REQUESTED",
        notes=payload.notes.strip() if payload.notes else None,
        created_by=str(current_user.id),
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.add(
        LogisticsReturnEvent(
            id=str(uuid4()),
            return_id=row.id,
            from_status=None,
            to_status="REQUESTED",
            reason="return created",
            changed_by=str(current_user.id),
            occurred_at=now,
            created_at=now,
        )
    )
    _audit_ops(
        db=db,
        action="LOGISTICS_RETURN_CREATE",
        result="SUCCESS",
        correlation_id=corr_id,
        user_id=str(current_user.id),
        details={"return_id": row.id, "order_id": order_id, "partner_id": partner_id, "reason_code": reason_code},
    )
    db.commit()
    return _to_return_out(row)


@router.get("/returns/{return_id}", response_model=LogisticsReturnOut)
def get_logistics_return(return_id: str, db: Session = Depends(get_db)):
    row = db.get(LogisticsReturn, return_id)
    if row is None:
        raise HTTPException(status_code=404, detail={"type": "RETURN_NOT_FOUND", "message": "Return não encontrado."})
    return _to_return_out(row)


@router.get("/returns", response_model=LogisticsReturnListOut)
def list_logistics_returns(
    partner_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    from_: str | None = Query(default=None, alias="from"),
    to: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(LogisticsReturn)
    normalized_partner = str(partner_id or "").strip()
    normalized_status = str(status or "").strip().upper()
    if normalized_partner:
        query = query.filter(LogisticsReturn.partner_id == normalized_partner)
    if normalized_status:
        if normalized_status not in _RETURN_STATUSES:
            raise HTTPException(status_code=422, detail={"type": "INVALID_RETURN_STATUS", "allowed_statuses": sorted(_RETURN_STATUSES)})
        query = query.filter(LogisticsReturn.status == normalized_status)
    from_dt = _parse_iso_datetime_utc_optional(from_, field_name="from")
    to_dt = _parse_iso_datetime_utc_optional(to, field_name="to")
    if from_dt and to_dt and from_dt > to_dt:
        raise HTTPException(status_code=422, detail={"type": "INVALID_DATE_RANGE", "message": "from deve ser <= to."})
    if from_dt:
        query = query.filter(LogisticsReturn.created_at >= from_dt)
    if to_dt:
        query = query.filter(LogisticsReturn.created_at <= to_dt)
    total = query.count()
    rows = query.order_by(LogisticsReturn.created_at.desc(), LogisticsReturn.id.desc()).offset(offset).limit(limit).all()
    return LogisticsReturnListOut(ok=True, total=total, items=[_to_return_out(row) for row in rows])


@router.patch("/returns/{return_id}/status", response_model=LogisticsReturnOut)
def patch_logistics_return_status(
    return_id: str,
    payload: LogisticsReturnStatusUpdateIn,
    current_user: User = Depends(get_current_user),
    correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    db: Session = Depends(get_db),
):
    corr_id = _resolve_correlation_id(correlation_id)
    row = db.get(LogisticsReturn, return_id)
    if row is None:
        raise HTTPException(status_code=404, detail={"type": "RETURN_NOT_FOUND", "message": "Return não encontrado."})
    to_status = payload.to_status.strip().upper()
    if to_status not in _RETURN_STATUSES:
        raise HTTPException(status_code=422, detail={"type": "INVALID_RETURN_STATUS", "allowed_statuses": sorted(_RETURN_STATUSES)})
    from_status = str(row.status or "").strip().upper()
    allowed_next = _RETURN_STATUS_TRANSITIONS.get(from_status, set())
    if to_status != from_status and to_status not in allowed_next:
        raise HTTPException(
            status_code=422,
            detail={
                "type": "INVALID_RETURN_STATUS_TRANSITION",
                "message": "Transição de status de return inválida.",
                "from_status": from_status,
                "to_status": to_status,
                "allowed_next": sorted(allowed_next),
            },
        )
    now = datetime.now(timezone.utc)
    reason = payload.reason.strip() if payload.reason else None
    before = {
        "id": row.id,
        "order_id": row.order_id,
        "partner_id": row.partner_id,
        "reason_code": row.reason_code,
        "status": from_status,
        "notes": row.notes,
        "updated_at": _to_iso_utc(row.updated_at),
    }
    row.status = to_status
    row.updated_at = now
    db.add(
        LogisticsReturnEvent(
            id=str(uuid4()),
            return_id=row.id,
            from_status=from_status,
            to_status=to_status,
            reason=reason,
            changed_by=str(current_user.id),
            occurred_at=now,
            created_at=now,
        )
    )
    enqueued_deliveries = 0
    if to_status != from_status:
        enqueued_deliveries = _enqueue_return_critical_webhooks(
            db=db,
            return_row=row,
            to_status=to_status,
        )
    after = {
        "id": row.id,
        "order_id": row.order_id,
        "partner_id": row.partner_id,
        "reason_code": row.reason_code,
        "status": to_status,
        "notes": row.notes,
        "updated_at": _to_iso_utc(row.updated_at),
    }

    _audit_ops(
        db=db,
        action="LOGISTICS_RETURN_STATUS_CHANGE",
        result="SUCCESS",
        correlation_id=corr_id,
        user_id=str(current_user.id),
        details={
            "partner_id": row.partner_id,
            "return_id": row.id,
            "before": before,
            "after": after,
            "transition": {"from_status": from_status, "to_status": to_status},
            "change_reason": reason,
            "webhook_deliveries_enqueued": enqueued_deliveries,
        },
    )
    db.commit()
    return _to_return_out(row)


@router.get("/returns/{return_id}/events", response_model=LogisticsReturnEventListOut)
def list_logistics_return_events(
    return_id: str,
    limit: int = Query(default=200, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    row = db.get(LogisticsReturn, return_id)
    if row is None:
        raise HTTPException(status_code=404, detail={"type": "RETURN_NOT_FOUND", "message": "Return não encontrado."})
    items = (
        db.query(LogisticsReturnEvent)
        .filter(LogisticsReturnEvent.return_id == return_id)
        .order_by(LogisticsReturnEvent.occurred_at.desc(), LogisticsReturnEvent.id.desc())
        .limit(limit)
        .all()
    )
    return LogisticsReturnEventListOut(ok=True, total=len(items), items=[_to_return_event_out(item) for item in items])


@router.post("/returns/{return_id}/simulate-delivery")
def post_logistics_return_simulate_delivery(
    return_id: str,
    current_user: User = Depends(get_current_user),
    correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    db: Session = Depends(get_db),
):
    corr_id = _resolve_correlation_id(correlation_id)
    row = db.get(LogisticsReturn, return_id)
    if row is None:
        raise HTTPException(status_code=404, detail={"type": "RETURN_NOT_FOUND", "message": "Return não encontrado."})
    normalized_status = str(row.status or "").strip().upper()
    if normalized_status not in {"RECEIVED", "CLOSED"}:
        raise HTTPException(
            status_code=409,
            detail={
                "type": "RETURN_STATUS_NOT_CRITICAL",
                "message": "Simulação de delivery exige status RECEIVED ou CLOSED.",
                "current_status": normalized_status,
            },
        )
    enqueued_deliveries = _enqueue_return_critical_webhooks(
        db=db,
        return_row=row,
        to_status=normalized_status,
    )
    _audit_ops(
        db=db,
        action="LOGISTICS_RETURN_WEBHOOK_SIMULATE_DELIVERY",
        result="SUCCESS",
        correlation_id=corr_id,
        user_id=str(current_user.id),
        details={
            "return_id": row.id,
            "status": normalized_status,
            "webhook_deliveries_enqueued": enqueued_deliveries,
        },
    )
    db.commit()
    return {"ok": True, "return_id": row.id, "status": normalized_status, "enqueued_deliveries": enqueued_deliveries}


@router.get("/ops/overview", response_model=LogisticsOpsOverviewOut)
def get_logistics_ops_overview(
    from_: str | None = Query(default=None, alias="from"),
    to: str | None = Query(default=None),
    carrier_code: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    now_utc = datetime.now(timezone.utc)
    current_to = _parse_iso_datetime_utc_optional(to, field_name="to") or now_utc
    current_from = _parse_iso_datetime_utc_optional(from_, field_name="from") or (current_to - timedelta(days=7))
    window_to = current_to
    window_from = current_from
    if window_from > window_to:
        raise HTTPException(status_code=422, detail={"type": "INVALID_DATE_RANGE", "message": "from deve ser <= to."})
    window_span = current_to - current_from
    previous_to = current_from
    previous_from = previous_to - window_span

    rows_current = (
        db.query(LogisticsTrackingEvent)
        .filter(LogisticsTrackingEvent.created_at >= current_from, LogisticsTrackingEvent.created_at <= current_to)
        .order_by(LogisticsTrackingEvent.created_at.desc())
        .limit(20000)
        .all()
    )
    rows_previous = (
        db.query(LogisticsTrackingEvent)
        .filter(LogisticsTrackingEvent.created_at >= previous_from, LogisticsTrackingEvent.created_at <= previous_to)
        .order_by(LogisticsTrackingEvent.created_at.desc())
        .limit(20000)
        .all()
    )
    filtered_rows = [r for r in rows_current if not carrier_code or r.source == f"CARRIER_{carrier_code.strip().upper()}"]
    filtered_rows_prev = [r for r in rows_previous if not carrier_code or r.source == f"CARRIER_{carrier_code.strip().upper()}"]
    event_counter = Counter([str(r.event_code or "").strip().upper() for r in filtered_rows if r.event_code])
    event_counter_prev = Counter([str(r.event_code or "").strip().upper() for r in filtered_rows_prev if r.event_code])

    attempts_current = (
        db.query(LogisticsDeliveryAttempt)
        .filter(LogisticsDeliveryAttempt.created_at >= current_from, LogisticsDeliveryAttempt.created_at <= current_to)
        .order_by(LogisticsDeliveryAttempt.created_at.desc())
        .limit(20000)
        .all()
    )
    attempts_previous = (
        db.query(LogisticsDeliveryAttempt)
        .filter(LogisticsDeliveryAttempt.created_at >= previous_from, LogisticsDeliveryAttempt.created_at <= previous_to)
        .order_by(LogisticsDeliveryAttempt.created_at.desc())
        .limit(20000)
        .all()
    )
    attempt_counter = Counter([str(r.status or "").strip().upper() for r in attempts_current if r.status])
    attempt_counter_prev = Counter([str(r.status or "").strip().upper() for r in attempts_previous if r.status])

    labels_current = (
        db.query(LogisticsShipmentLabel)
        .filter(LogisticsShipmentLabel.created_at >= current_from, LogisticsShipmentLabel.created_at <= current_to)
        .order_by(LogisticsShipmentLabel.created_at.desc())
        .limit(20000)
        .all()
    )
    labels_previous = (
        db.query(LogisticsShipmentLabel)
        .filter(LogisticsShipmentLabel.created_at >= previous_from, LogisticsShipmentLabel.created_at <= previous_to)
        .order_by(LogisticsShipmentLabel.created_at.desc())
        .limit(20000)
        .all()
    )
    label_counter = Counter([str(r.carrier_code or "").strip().upper() for r in labels_current if r.carrier_code])
    label_counter_prev = Counter([str(r.carrier_code or "").strip().upper() for r in labels_previous if r.carrier_code])

    return LogisticsOpsOverviewOut(
        ok=True,
        **{"from": _to_iso_utc(window_from), "to": _to_iso_utc(window_to)},
        carrier_code=(carrier_code.strip().upper() if carrier_code else None),
        totals={
            "events": len(filtered_rows),
            "events_previous": len(filtered_rows_prev),
            "attempts": len(attempts_current),
            "attempts_previous": len(attempts_previous),
            "labels": len(labels_current),
            "labels_previous": len(labels_previous),
        },
        by_event_code=_with_trend(event_counter, event_counter_prev),
        by_attempt_status=_with_trend(attempt_counter, attempt_counter_prev),
        by_label_carrier=_with_trend(label_counter, label_counter_prev),
    )


@router.get("/ops/manifests/overview", response_model=LogisticsManifestOpsOverviewOut)
def get_logistics_manifests_ops_overview(
    from_: str | None = Query(default=None, alias="from"),
    to: str | None = Query(default=None),
    partner_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    now_utc = datetime.now(timezone.utc)
    current_to = _parse_iso_datetime_utc_optional(to, field_name="to") or now_utc
    current_from = _parse_iso_datetime_utc_optional(from_, field_name="from") or (current_to - timedelta(days=7))
    if current_from > current_to:
        raise HTTPException(status_code=422, detail={"type": "INVALID_DATE_RANGE", "message": "from deve ser <= to."})

    window_span = current_to - current_from
    previous_to = current_from
    previous_from = previous_to - window_span

    normalized_partner = str(partner_id or "").strip()

    query_current = db.query(LogisticsManifest).filter(
        LogisticsManifest.created_at >= current_from,
        LogisticsManifest.created_at <= current_to,
    )
    query_previous = db.query(LogisticsManifest).filter(
        LogisticsManifest.created_at >= previous_from,
        LogisticsManifest.created_at <= previous_to,
    )
    if normalized_partner:
        query_current = query_current.filter(LogisticsManifest.logistics_partner_id == normalized_partner)
        query_previous = query_previous.filter(LogisticsManifest.logistics_partner_id == normalized_partner)

    current_rows = query_current.order_by(LogisticsManifest.created_at.desc()).limit(20000).all()
    previous_rows = query_previous.order_by(LogisticsManifest.created_at.desc()).limit(20000).all()

    current_status_counter = Counter([str(row.status or "").strip().upper() for row in current_rows if row.status])
    previous_status_counter = Counter([str(row.status or "").strip().upper() for row in previous_rows if row.status])

    pending_like = int(current_status_counter.get("PENDING", 0) + current_status_counter.get("IN_TRANSIT", 0))
    partial_or_failed = int(current_status_counter.get("PARTIAL", 0) + current_status_counter.get("FAILED", 0))
    total_current = len(current_rows)
    partial_failed_rate = (partial_or_failed / total_current * 100.0) if total_current > 0 else 0.0

    alerts: list[dict] = []
    if pending_like >= 20:
        alerts.append(
            {
                "type": "L3_MANIFEST_BACKLOG_HIGH",
                "severity": "HIGH",
                "threshold": 20,
                "value": pending_like,
                "message": "Backlog de manifestos em PENDING/IN_TRANSIT acima do limiar operacional.",
            }
        )
    if partial_failed_rate >= 25.0:
        alerts.append(
            {
                "type": "L3_MANIFEST_PARTIAL_FAILED_RATE_HIGH",
                "severity": "HIGH",
                "threshold": 25.0,
                "value": round(partial_failed_rate, 2),
                "message": "Taxa de manifestos PARTIAL/FAILED acima do limiar operacional.",
            }
        )

    confidence_badge = "HIGH"
    if alerts:
        confidence_badge = "LOW"
    elif pending_like >= 8 or partial_failed_rate >= 10.0:
        confidence_badge = "MEDIUM"

    return LogisticsManifestOpsOverviewOut(
        ok=True,
        **{"from": _to_iso_utc(current_from), "to": _to_iso_utc(current_to)},
        partner_id=normalized_partner or None,
        confidence_badge=confidence_badge,
        totals={
            "current_total": total_current,
            "previous_total": len(previous_rows),
            "pending_or_in_transit": pending_like,
            "partial_or_failed": partial_or_failed,
            "partial_failed_rate_pct": round(partial_failed_rate, 2),
        },
        by_status=_with_trend(current_status_counter, previous_status_counter),
        alerts=alerts,
    )


@router.get("/ops/manifests/view", response_class=HTMLResponse)
def get_logistics_manifests_ops_view() -> HTMLResponse:
    html = """
<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <title>ELLAN LAB Logistics Manifests OPS</title>
    <style>
      body { font-family: Inter, Arial, sans-serif; margin: 24px; background:#F8FAFC; color:#0F172A; }
      h1 { margin: 0 0 12px 0; font-size: 24px; }
      .row { display:flex; gap:10px; flex-wrap:wrap; margin-bottom: 12px; }
      input, button { padding:8px 10px; border:1px solid #CBD5E1; border-radius:8px; background:#fff; }
      button { background:#1D4ED8; color:#fff; border:none; cursor:pointer; }
      .cards { display:grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap:12px; margin: 16px 0; }
      .card { background:#fff; border:1px solid #E2E8F0; border-radius:12px; padding:12px; }
      .label { color:#475569; font-size:12px; text-transform: uppercase; letter-spacing: .04em; }
      .value { font-size:24px; font-weight:700; margin-top:6px; }
      .badge { font-size: 20px; font-weight: 800; }
      pre { background:#0B1220; color:#E2E8F0; border-radius:12px; padding:12px; overflow:auto; font-size:12px; }
    </style>
  </head>
  <body>
    <h1>OPS Logistics Manifests (L-3)</h1>
    <div class="row">
      <input id="from" placeholder="from ISO-8601 opcional" size="30" />
      <input id="to" placeholder="to ISO-8601 opcional" size="30" />
      <input id="partnerId" placeholder="partner_id opcional" size="20" />
      <button onclick="loadData()">Atualizar</button>
    </div>
    <div class="cards">
      <div class="card"><div class="label">Current Total</div><div id="currentTotal" class="value">-</div></div>
      <div class="card"><div class="label">Backlog Pending/In Transit</div><div id="pendingLike" class="value">-</div></div>
      <div class="card"><div class="label">Partial/Failed %</div><div id="partialFailedRate" class="value">-</div></div>
      <div class="card"><div class="label">Confidence</div><div id="confidenceBadge" class="badge">-</div></div>
    </div>
    <pre id="payload">Carregando...</pre>
    <script>
      async function loadData() {
        const params = new URLSearchParams();
        const from = document.getElementById('from').value.trim();
        const to = document.getElementById('to').value.trim();
        const partnerId = document.getElementById('partnerId').value.trim();
        if (from) params.set('from', from);
        if (to) params.set('to', to);
        if (partnerId) params.set('partner_id', partnerId);
        const resp = await fetch('/logistics/ops/manifests/overview?' + params.toString());
        const data = await resp.json();
        document.getElementById('payload').textContent = JSON.stringify(data, null, 2);
        document.getElementById('currentTotal').textContent = data?.totals?.current_total ?? '-';
        document.getElementById('pendingLike').textContent = data?.totals?.pending_or_in_transit ?? '-';
        document.getElementById('partialFailedRate').textContent = `${data?.totals?.partial_failed_rate_pct ?? '-'}%`;
        document.getElementById('confidenceBadge').textContent = data?.confidence_badge ?? '-';
      }
      loadData();
    </script>
  </body>
</html>
"""
    return HTMLResponse(content=html)


@router.get("/ops/view", response_class=HTMLResponse)
def get_logistics_ops_view() -> HTMLResponse:
    html = """
<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <title>ELLAN LAB Logistics OPS</title>
    <style>
      body { font-family: Inter, Arial, sans-serif; margin: 24px; background:#F8FAFC; color:#0F172A; }
      h1 { margin: 0 0 12px 0; font-size: 24px; }
      .row { display:flex; gap:10px; flex-wrap:wrap; margin-bottom: 12px; }
      input, button { padding:8px 10px; border:1px solid #CBD5E1; border-radius:8px; background:#fff; }
      button { background:#1D4ED8; color:#fff; border:none; cursor:pointer; }
      .cards { display:grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap:12px; margin: 16px 0; }
      .card { background:#fff; border:1px solid #E2E8F0; border-radius:12px; padding:12px; }
      .label { color:#475569; font-size:12px; text-transform: uppercase; letter-spacing: .04em; }
      .value { font-size:24px; font-weight:700; margin-top:6px; }
      pre { background:#0B1220; color:#E2E8F0; border-radius:12px; padding:12px; overflow:auto; font-size:12px; }
    </style>
  </head>
  <body>
    <h1>OPS Logistics (L-1)</h1>
    <div class="row">
      <input id="from" placeholder="from ISO-8601 opcional" size="30" />
      <input id="to" placeholder="to ISO-8601 opcional" size="30" />
      <input id="carrierCode" placeholder="carrier_code opcional" size="20" />
      <button onclick="loadData()">Atualizar</button>
    </div>
    <div class="cards">
      <div class="card"><div class="label">Tracking Events</div><div id="events" class="value">-</div></div>
      <div class="card"><div class="label">Delivery Attempts</div><div id="attempts" class="value">-</div></div>
      <div class="card"><div class="label">Shipment Labels</div><div id="labels" class="value">-</div></div>
    </div>
    <pre id="payload">Carregando...</pre>
    <script>
      async function loadData() {
        const params = new URLSearchParams();
        const from = document.getElementById('from').value.trim();
        const to = document.getElementById('to').value.trim();
        const carrier = document.getElementById('carrierCode').value.trim();
        if (from) params.set('from', from);
        if (to) params.set('to', to);
        if (carrier) params.set('carrier_code', carrier);
        const resp = await fetch('/logistics/ops/overview?' + params.toString());
        const data = await resp.json();
        document.getElementById('payload').textContent = JSON.stringify(data, null, 2);
        document.getElementById('events').textContent = data?.totals?.events ?? '-';
        document.getElementById('attempts').textContent = data?.totals?.attempts ?? '-';
        document.getElementById('labels').textContent = data?.totals?.labels ?? '-';
      }
      loadData();
    </script>
  </body>
</html>
"""
    return HTMLResponse(content=html)
