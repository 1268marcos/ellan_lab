from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import hashlib
import json
import secrets
from decimal import Decimal
from collections import Counter
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.auth_dep import get_current_user, require_user_roles
from app.core.db import get_db
from app.models.ops_action_audit import OpsActionAudit
from app.models.partner_api_key import PartnerApiKey
from app.models.partner_contact import PartnerContact
from app.models.partner_webhook_delivery import PartnerWebhookDelivery
from app.models.partner_integration_health import PartnerIntegrationHealth
from app.models.partner_sla_agreement import PartnerSlaAgreement
from app.models.partner_status_history import PartnerStatusHistory
from app.models.partner_webhook_endpoint import PartnerWebhookEndpoint
from app.models.user import User
from app.services.ops_audit_service import record_ops_action_audit
from app.schemas.partners import (
    PartnerContactPatchIn,
    PartnerContactIn,
    PartnerContactListOut,
    PartnerContactOut,
    PartnerApiKeyCreateOut,
    PartnerApiKeyIn,
    PartnerApiKeyListOut,
    PartnerApiKeyOut,
    PartnerDeleteOut,
    PartnerIntegrationHealthIn,
    PartnerIntegrationHealthListOut,
    PartnerIntegrationHealthOut,
    PartnerOpsActionsOut,
    PartnerOpsAuditItemOut,
    PartnerOpsAuditListOut,
    PartnerOpsBadgeLegendItemOut,
    PartnerOpsCompareCardOut,
    PartnerOpsCompareOut,
    PartnerOpsDashboardOut,
    PartnerOpsChangeDailyOut,
    PartnerOpsChangeDistributionItemOut,
    PartnerOpsChangesSeriesOut,
    PartnerOpsKpiCountOut,
    PartnerOpsKpiErrorDailyOut,
    PartnerOpsKpiTopPartnerOut,
    PartnerOpsKpisOut,
    PartnerSlaAgreementPatchIn,
    PartnerSlaAgreementIn,
    PartnerSlaAgreementListOut,
    PartnerSlaAgreementOut,
    PartnerStatusHistoryItemOut,
    PartnerStatusHistoryListOut,
    PartnerStatusOut,
    PartnerStatusTransitionIn,
    PartnerWebhookEndpointIn,
    PartnerWebhookEndpointListOut,
    PartnerWebhookEndpointOut,
    PartnerWebhookDeliveryListOut,
    PartnerWebhookDeliveryOut,
    PartnerWebhookDeliveryTestIn,
)

router = APIRouter(
    prefix="/partners",
    tags=["partners"],
    dependencies=[Depends(require_user_roles(allowed_roles={"admin_operacao", "auditoria"}))],
)

_PARTNER_STATUSES = {
    "DRAFT",
    "PENDING_REVIEW",
    "ACTIVE",
    "SUSPENDED",
    "TERMINATED",
}

_CONTACT_TYPES = {"COMMERCIAL", "TECHNICAL", "BILLING", "EMERGENCY"}
_HEALTH_STATUSES = {"UP", "DOWN", "DEGRADED", "TIMEOUT"}

_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "DRAFT": {"PENDING_REVIEW", "TERMINATED"},
    "PENDING_REVIEW": {"ACTIVE", "SUSPENDED", "TERMINATED"},
    "ACTIVE": {"SUSPENDED", "TERMINATED"},
    "SUSPENDED": {"ACTIVE", "TERMINATED"},
    "TERMINATED": set(),
}


def _to_iso_utc(value: datetime | None) -> str:
    if value is None:
        return datetime.now(timezone.utc).isoformat()
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def _load_partner_status(db: Session, partner_id: str) -> str:
    row = db.execute(
        text("SELECT id, status FROM ecommerce_partners WHERE id = :id"),
        {"id": partner_id},
    ).mappings().first()
    if not row:
        raise HTTPException(
            status_code=404,
            detail={
                "type": "PARTNER_NOT_FOUND",
                "message": "Parceiro de e-commerce não encontrado.",
                "partner_id": partner_id,
            },
        )
    return str(row.get("status") or "DRAFT")


def _parse_iso_date(raw_value: str, *, field_name: str) -> date:
    value = str(raw_value or "").strip()
    if not value:
        raise HTTPException(
            status_code=422,
            detail={"type": "INVALID_DATE", "message": f"{field_name} é obrigatório."},
        )
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={"type": "INVALID_DATE", "message": f"{field_name} deve estar no formato YYYY-MM-DD."},
        ) from exc


def _parse_iso_datetime_utc(raw_value: str, *, field_name: str) -> datetime:
    value = str(raw_value or "").strip()
    if not value:
        raise HTTPException(
            status_code=422,
            detail={"type": "INVALID_DATE_RANGE", "message": f"{field_name} é obrigatório."},
        )
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={"type": "INVALID_DATE_RANGE", "message": f"{field_name} inválido. Use ISO-8601."},
        ) from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _parse_iso_datetime_utc_optional(raw_value: str | None, *, field_name: str) -> datetime | None:
    value = str(raw_value or "").strip()
    if not value:
        return None
    return _parse_iso_datetime_utc(value, field_name=field_name)


def _gen_api_key_plain() -> tuple[str, str]:
    suffix = secrets.token_urlsafe(24).replace("-", "").replace("_", "")
    plain = f"elln_pk_{suffix}"
    return plain[:120], plain[:12]


def _hash_secret(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _json_load_list(value: str | None, default: list[str] | None = None) -> list[str]:
    if default is None:
        default = []
    try:
        parsed = json.loads(str(value or "[]"))
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
        return default
    except Exception:
        return default


def _json_load_dict(value: str | None, default: dict | None = None) -> dict:
    if default is None:
        default = {}
    try:
        parsed = json.loads(str(value or "{}"))
        if isinstance(parsed, dict):
            return parsed
        return default
    except Exception:
        return default


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
        # Não deve quebrar a operação principal por falha de auditoria
        pass


def _resolve_change_type(action: str) -> str:
    normalized = str(action or "").strip().upper()
    if normalized.startswith("PARTNER_STATUS_"):
        return "status"
    if normalized.startswith("PARTNER_CONTACT_"):
        return "contact"
    if normalized.startswith("PARTNER_SLA_"):
        return "sla"
    return "other"


def _safe_delta_pct(current: int, previous: int) -> float:
    if previous <= 0:
        if current <= 0:
            return 0.0
        return 100.0
    return round(((current - previous) / previous) * 100, 2)


def _collect_change_type_counter(rows: list[OpsActionAudit]) -> Counter[str]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter[_resolve_change_type(row.action)] += 1
    return counter


def _resolve_confidence_and_note(*, total_current: int, total_previous: int) -> tuple[str, str]:
    min_volume = min(total_current, total_previous)
    if min_volume < 10:
        return (
            "LOW",
            "Base de eventos muito pequena no período comparado; variações percentuais podem oscilar bastante.",
        )
    if min_volume < 30:
        return (
            "MEDIUM",
            "Base de eventos moderada; use a variação percentual junto com os valores absolutos.",
        )
    return (
        "HIGH",
        "Base de eventos suficiente para leitura mais estável das tendências percentuais.",
    )


def _resolve_confidence_badge(confidence_level: str) -> PartnerOpsBadgeLegendItemOut:
    level = str(confidence_level or "").upper()
    if level == "LOW":
        return PartnerOpsBadgeLegendItemOut(
            key="confidence_low",
            label="Confianca baixa",
            color="#DC2626",
            icon="alert-triangle",
        )
    if level == "MEDIUM":
        return PartnerOpsBadgeLegendItemOut(
            key="confidence_medium",
            label="Confianca moderada",
            color="#D97706",
            icon="alert-circle",
        )
    return PartnerOpsBadgeLegendItemOut(
        key="confidence_high",
        label="Confianca alta",
        color="#16A34A",
        icon="check-circle",
    )


def _build_data_quality_flags(*, total_current: int, total_previous: int) -> list[str]:
    flags: list[str] = []
    if total_current == 0 and total_previous == 0:
        flags.append("NO_EVENTS_BOTH_WINDOWS")
    elif total_current == 0:
        flags.append("NO_EVENTS_CURRENT_WINDOW")
    elif total_previous == 0:
        flags.append("NO_EVENTS_PREVIOUS_WINDOW")

    min_volume = min(total_current, total_previous)
    if min_volume < 10:
        flags.append("LOW_VOLUME_BASELINE")
    elif min_volume < 30:
        flags.append("MEDIUM_VOLUME_BASELINE")
    return flags


def _extract_partner_id(details: dict) -> str | None:
    if not isinstance(details, dict):
        return None
    partner_id = (
        details.get("partner_id")
        or (details.get("before", {}) or {}).get("partner_id")
        or (details.get("after", {}) or {}).get("partner_id")
    )
    if partner_id is None:
        return None
    value = str(partner_id).strip()
    return value or None


def _parse_include_sections(raw_value: str | None) -> list[str]:
    allowed = {"kpis", "compare", "changes_series"}
    if raw_value is None or not str(raw_value).strip():
        return ["kpis", "compare", "changes_series"]

    parts = [
        part.strip().lower()
        for part in str(raw_value).split(",")
        if part.strip()
    ]
    if not parts:
        return ["kpis", "compare", "changes_series"]

    invalid = sorted({part for part in parts if part not in allowed})
    if invalid:
        raise HTTPException(
            status_code=422,
            detail={
                "type": "INVALID_INCLUDE_SECTIONS",
                "message": "include_sections possui valores inválidos.",
                "allowed_sections": sorted(allowed),
                "invalid_sections": invalid,
            },
        )

    # Remove duplicados mantendo ordem.
    unique_parts: list[str] = []
    seen = set()
    for part in parts:
        if part in seen:
            continue
        seen.add(part)
        unique_parts.append(part)
    return unique_parts


@router.post("/{partner_id}/api-keys", response_model=PartnerApiKeyCreateOut)
def post_partner_api_key(
    partner_id: str,
    payload: PartnerApiKeyIn,
    current_user: User = Depends(get_current_user),
    correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    db: Session = Depends(get_db),
):
    corr_id = _resolve_correlation_id(correlation_id)
    _load_partner_status(db, partner_id=partner_id)

    plain_key, key_prefix = _gen_api_key_plain()
    row = PartnerApiKey(
        id=str(uuid4()),
        partner_id=partner_id,
        partner_type="ECOMMERCE",
        key_prefix=key_prefix,
        key_hash=_hash_secret(plain_key),
        label=(payload.label.strip() if payload.label else None),
        scopes_json=json.dumps(payload.scopes or []),
        expires_at=_parse_iso_datetime_utc_optional(payload.expires_at, field_name="expires_at"),
        created_by=str(current_user.id),
        created_at=datetime.now(timezone.utc),
    )
    db.add(row)
    _audit_ops(
        db=db,
        action="PARTNER_API_KEY_CREATE",
        result="SUCCESS",
        correlation_id=corr_id,
        user_id=str(current_user.id),
        details={
            "partner_id": partner_id,
            "after": {
                "id": row.id,
                "key_prefix": row.key_prefix,
                "label": row.label,
                "scopes": payload.scopes or [],
                "expires_at": _to_iso_utc(row.expires_at) if row.expires_at else None,
            },
        },
    )
    db.commit()

    item = PartnerApiKeyOut(
        id=row.id,
        partner_id=row.partner_id,
        partner_type=row.partner_type,
        key_prefix=row.key_prefix,
        label=row.label,
        scopes=_json_load_list(row.scopes_json),
        expires_at=_to_iso_utc(row.expires_at) if row.expires_at else None,
        last_used_at=_to_iso_utc(row.last_used_at) if row.last_used_at else None,
        revoked_at=_to_iso_utc(row.revoked_at) if row.revoked_at else None,
        created_at=_to_iso_utc(row.created_at),
    )
    return PartnerApiKeyCreateOut(
        ok=True,
        message="API key gerada. O valor plain é retornado somente uma vez.",
        api_key=plain_key,
        item=item,
    )


@router.get("/{partner_id}/api-keys", response_model=PartnerApiKeyListOut)
def get_partner_api_keys(
    partner_id: str,
    include_revoked: bool = Query(default=False),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    _load_partner_status(db, partner_id=partner_id)
    query = db.query(PartnerApiKey).filter(
        PartnerApiKey.partner_id == partner_id,
        PartnerApiKey.partner_type == "ECOMMERCE",
    )
    if not include_revoked:
        query = query.filter(PartnerApiKey.revoked_at.is_(None))
    rows = (
        query.order_by(PartnerApiKey.created_at.desc(), PartnerApiKey.id.desc())
        .limit(limit)
        .all()
    )
    items = [
        PartnerApiKeyOut(
            id=row.id,
            partner_id=row.partner_id,
            partner_type=row.partner_type,
            key_prefix=row.key_prefix,
            label=row.label,
            scopes=_json_load_list(row.scopes_json),
            expires_at=_to_iso_utc(row.expires_at) if row.expires_at else None,
            last_used_at=_to_iso_utc(row.last_used_at) if row.last_used_at else None,
            revoked_at=_to_iso_utc(row.revoked_at) if row.revoked_at else None,
            created_at=_to_iso_utc(row.created_at),
        )
        for row in rows
    ]
    return PartnerApiKeyListOut(ok=True, total=len(items), items=items)


@router.delete("/{partner_id}/api-keys/{key_id}", response_model=PartnerDeleteOut)
def delete_partner_api_key(
    partner_id: str,
    key_id: str,
    current_user: User = Depends(get_current_user),
    correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    db: Session = Depends(get_db),
):
    corr_id = _resolve_correlation_id(correlation_id)
    _load_partner_status(db, partner_id=partner_id)
    row = db.get(PartnerApiKey, key_id)
    if not row or row.partner_id != partner_id or row.partner_type != "ECOMMERCE":
        raise HTTPException(status_code=404, detail={"type": "API_KEY_NOT_FOUND", "message": "API key não encontrada."})
    row.revoked_at = datetime.now(timezone.utc)
    _audit_ops(
        db=db,
        action="PARTNER_API_KEY_REVOKE",
        result="SUCCESS",
        correlation_id=corr_id,
        user_id=str(current_user.id),
        details={"partner_id": partner_id, "key_id": key_id},
    )
    db.commit()
    return PartnerDeleteOut(ok=True, id=key_id, message="API key revogada.")


@router.post("/{partner_id}/webhooks", response_model=PartnerWebhookEndpointOut)
def post_partner_webhook(
    partner_id: str,
    payload: PartnerWebhookEndpointIn,
    current_user: User = Depends(get_current_user),
    correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    db: Session = Depends(get_db),
):
    corr_id = _resolve_correlation_id(correlation_id)
    _load_partner_status(db, partner_id=partner_id)
    now = datetime.now(timezone.utc)
    row = PartnerWebhookEndpoint(
        id=str(uuid4()),
        partner_id=partner_id,
        partner_type="ECOMMERCE",
        url=payload.url.strip(),
        secret_hash=_hash_secret(payload.secret),
        secret_key=payload.secret,
        events_json=json.dumps(payload.events or ["*"]),
        api_version=payload.api_version.strip() or "v1",
        active=bool(payload.active),
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    _audit_ops(
        db=db,
        action="PARTNER_WEBHOOK_CREATE",
        result="SUCCESS",
        correlation_id=corr_id,
        user_id=str(current_user.id),
        details={"partner_id": partner_id, "after": {"id": row.id, "url": row.url, "events": payload.events or ["*"], "api_version": row.api_version, "active": row.active}},
    )
    db.commit()
    return PartnerWebhookEndpointOut(
        id=row.id,
        partner_id=row.partner_id,
        partner_type=row.partner_type,
        url=row.url,
        events=_json_load_list(row.events_json, ["*"]),
        api_version=row.api_version,
        active=bool(row.active),
        created_at=_to_iso_utc(row.created_at),
        updated_at=_to_iso_utc(row.updated_at),
    )


@router.get("/{partner_id}/webhooks", response_model=PartnerWebhookEndpointListOut)
def get_partner_webhooks(
    partner_id: str,
    only_active: bool = Query(default=False),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    _load_partner_status(db, partner_id=partner_id)
    query = db.query(PartnerWebhookEndpoint).filter(
        PartnerWebhookEndpoint.partner_id == partner_id,
        PartnerWebhookEndpoint.partner_type == "ECOMMERCE",
    )
    if only_active:
        query = query.filter(PartnerWebhookEndpoint.active.is_(True))
    rows = (
        query.order_by(PartnerWebhookEndpoint.created_at.desc(), PartnerWebhookEndpoint.id.desc())
        .limit(limit)
        .all()
    )
    items = [
        PartnerWebhookEndpointOut(
            id=row.id,
            partner_id=row.partner_id,
            partner_type=row.partner_type,
            url=row.url,
            events=_json_load_list(row.events_json, ["*"]),
            api_version=row.api_version,
            active=bool(row.active),
            created_at=_to_iso_utc(row.created_at),
            updated_at=_to_iso_utc(row.updated_at),
        )
        for row in rows
    ]
    return PartnerWebhookEndpointListOut(ok=True, total=len(items), items=items)


@router.post("/{partner_id}/webhooks/{wh_id}/deliveries/test", response_model=PartnerWebhookDeliveryOut)
def post_partner_webhook_delivery_test(
    partner_id: str,
    wh_id: str,
    payload: PartnerWebhookDeliveryTestIn,
    current_user: User = Depends(get_current_user),
    correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    db: Session = Depends(get_db),
):
    corr_id = _resolve_correlation_id(correlation_id)
    _load_partner_status(db, partner_id=partner_id)
    endpoint = db.get(PartnerWebhookEndpoint, wh_id)
    if not endpoint or endpoint.partner_id != partner_id or endpoint.partner_type != "ECOMMERCE":
        raise HTTPException(status_code=404, detail={"type": "WEBHOOK_ENDPOINT_NOT_FOUND", "message": "Webhook endpoint não encontrado."})

    payload_json = json.dumps(payload.payload or {})
    delivery = PartnerWebhookDelivery(
        id=str(uuid4()),
        endpoint_id=endpoint.id,
        event_id=str(uuid4()),
        event_type=payload.event_type.strip(),
        payload_json=payload_json,
        payload_hash=_hash_secret(payload_json),
        status="PENDING",
        attempt_count=0,
        next_retry_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
    )
    db.add(delivery)
    _audit_ops(
        db=db,
        action="PARTNER_WEBHOOK_DELIVERY_ENQUEUE_TEST",
        result="SUCCESS",
        correlation_id=corr_id,
        user_id=str(current_user.id),
        details={"partner_id": partner_id, "webhook_id": wh_id, "delivery_id": delivery.id, "event_type": delivery.event_type},
    )
    db.commit()
    return PartnerWebhookDeliveryOut(
        id=delivery.id,
        endpoint_id=delivery.endpoint_id,
        event_id=delivery.event_id,
        event_type=delivery.event_type,
        http_status=delivery.http_status,
        attempt_count=int(delivery.attempt_count or 0),
        status=delivery.status,
        last_error=delivery.last_error,
        next_retry_at=_to_iso_utc(delivery.next_retry_at) if delivery.next_retry_at else None,
        delivered_at=_to_iso_utc(delivery.delivered_at) if delivery.delivered_at else None,
        created_at=_to_iso_utc(delivery.created_at),
    )


@router.get("/{partner_id}/webhooks/{wh_id}/deliveries", response_model=PartnerWebhookDeliveryListOut)
def get_partner_webhook_deliveries(
    partner_id: str,
    wh_id: str,
    status: str | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    _load_partner_status(db, partner_id=partner_id)
    endpoint = db.get(PartnerWebhookEndpoint, wh_id)
    if not endpoint or endpoint.partner_id != partner_id or endpoint.partner_type != "ECOMMERCE":
        raise HTTPException(status_code=404, detail={"type": "WEBHOOK_ENDPOINT_NOT_FOUND", "message": "Webhook endpoint não encontrado."})

    query = db.query(PartnerWebhookDelivery).filter(PartnerWebhookDelivery.endpoint_id == wh_id)
    if status:
        query = query.filter(PartnerWebhookDelivery.status == status.strip().upper())
    rows = (
        query.order_by(PartnerWebhookDelivery.created_at.desc(), PartnerWebhookDelivery.id.desc())
        .limit(limit)
        .all()
    )
    items = [
        PartnerWebhookDeliveryOut(
            id=row.id,
            endpoint_id=row.endpoint_id,
            event_id=row.event_id,
            event_type=row.event_type,
            http_status=row.http_status,
            attempt_count=int(row.attempt_count or 0),
            status=row.status,
            last_error=row.last_error,
            next_retry_at=_to_iso_utc(row.next_retry_at) if row.next_retry_at else None,
            delivered_at=_to_iso_utc(row.delivered_at) if row.delivered_at else None,
            created_at=_to_iso_utc(row.created_at),
        )
        for row in rows
    ]
    return PartnerWebhookDeliveryListOut(ok=True, total=len(items), items=items)


@router.post("/{partner_id}/webhooks/{wh_id}/deliveries/{delivery_id}/retry", response_model=PartnerWebhookDeliveryOut)
def post_partner_webhook_delivery_retry(
    partner_id: str,
    wh_id: str,
    delivery_id: str,
    current_user: User = Depends(get_current_user),
    correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    db: Session = Depends(get_db),
):
    corr_id = _resolve_correlation_id(correlation_id)
    _load_partner_status(db, partner_id=partner_id)
    endpoint = db.get(PartnerWebhookEndpoint, wh_id)
    if not endpoint or endpoint.partner_id != partner_id or endpoint.partner_type != "ECOMMERCE":
        raise HTTPException(status_code=404, detail={"type": "WEBHOOK_ENDPOINT_NOT_FOUND", "message": "Webhook endpoint não encontrado."})
    row = db.get(PartnerWebhookDelivery, delivery_id)
    if not row or row.endpoint_id != wh_id:
        raise HTTPException(status_code=404, detail={"type": "WEBHOOK_DELIVERY_NOT_FOUND", "message": "Webhook delivery não encontrado."})

    row.status = "FAILED"
    row.next_retry_at = datetime.now(timezone.utc)
    row.processing_started_at = None
    _audit_ops(
        db=db,
        action="PARTNER_WEBHOOK_DELIVERY_RETRY",
        result="SUCCESS",
        correlation_id=corr_id,
        user_id=str(current_user.id),
        details={"partner_id": partner_id, "webhook_id": wh_id, "delivery_id": delivery_id},
    )
    db.commit()
    return PartnerWebhookDeliveryOut(
        id=row.id,
        endpoint_id=row.endpoint_id,
        event_id=row.event_id,
        event_type=row.event_type,
        http_status=row.http_status,
        attempt_count=int(row.attempt_count or 0),
        status=row.status,
        last_error=row.last_error,
        next_retry_at=_to_iso_utc(row.next_retry_at) if row.next_retry_at else None,
        delivered_at=_to_iso_utc(row.delivered_at) if row.delivered_at else None,
        created_at=_to_iso_utc(row.created_at),
    )


@router.post("/{partner_id}/health/checks", response_model=PartnerIntegrationHealthOut)
def post_partner_health_check(
    partner_id: str,
    payload: PartnerIntegrationHealthIn,
    current_user: User = Depends(get_current_user),
    correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    db: Session = Depends(get_db),
):
    corr_id = _resolve_correlation_id(correlation_id)
    _load_partner_status(db, partner_id=partner_id)
    status = str(payload.status or "").strip().upper()
    if status not in _HEALTH_STATUSES:
        raise HTTPException(
            status_code=422,
            detail={
                "type": "INVALID_HEALTH_STATUS",
                "message": "Status de health inválido.",
                "allowed_statuses": sorted(_HEALTH_STATUSES),
            },
        )
    row = PartnerIntegrationHealth(
        partner_id=partner_id,
        partner_type="ECOMMERCE",
        endpoint_url=(payload.endpoint_url.strip() if payload.endpoint_url else None),
        checked_at=datetime.now(timezone.utc),
        status=status,
        latency_ms=payload.latency_ms,
        http_status=payload.http_status,
        error_message=(payload.error_message.strip() if payload.error_message else None),
    )
    db.add(row)
    db.flush()
    _audit_ops(
        db=db,
        action="PARTNER_HEALTH_CHECK_CREATE",
        result="SUCCESS",
        correlation_id=corr_id,
        user_id=str(current_user.id),
        details={"partner_id": partner_id, "after": {"id": row.id, "status": row.status, "latency_ms": row.latency_ms, "http_status": row.http_status}},
    )
    db.commit()
    return PartnerIntegrationHealthOut(
        id=int(row.id),
        partner_id=row.partner_id,
        partner_type=row.partner_type,
        endpoint_url=row.endpoint_url,
        checked_at=_to_iso_utc(row.checked_at),
        status=row.status,
        latency_ms=row.latency_ms,
        http_status=row.http_status,
        error_message=row.error_message,
    )


@router.get("/{partner_id}/health", response_model=PartnerIntegrationHealthListOut)
def get_partner_health(
    partner_id: str,
    from_: str | None = Query(default=None, alias="from"),
    to: str | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    _load_partner_status(db, partner_id=partner_id)
    query = db.query(PartnerIntegrationHealth).filter(
        PartnerIntegrationHealth.partner_id == partner_id,
        PartnerIntegrationHealth.partner_type == "ECOMMERCE",
    )
    if from_:
        query = query.filter(PartnerIntegrationHealth.checked_at >= _parse_iso_datetime_utc(from_, field_name="from"))
    if to:
        query = query.filter(PartnerIntegrationHealth.checked_at <= _parse_iso_datetime_utc(to, field_name="to"))
    rows = (
        query.order_by(PartnerIntegrationHealth.checked_at.desc(), PartnerIntegrationHealth.id.desc())
        .limit(limit)
        .all()
    )
    items = [
        PartnerIntegrationHealthOut(
            id=int(row.id),
            partner_id=row.partner_id,
            partner_type=row.partner_type,
            endpoint_url=row.endpoint_url,
            checked_at=_to_iso_utc(row.checked_at),
            status=row.status,
            latency_ms=row.latency_ms,
            http_status=row.http_status,
            error_message=row.error_message,
        )
        for row in rows
    ]
    return PartnerIntegrationHealthListOut(ok=True, total=len(items), items=items)


@router.get("/ops/audit", response_model=PartnerOpsAuditListOut)
def get_partners_ops_audit(
    partner_id: str | None = Query(default=None),
    action: str | None = Query(default=None),
    correlation_id: str | None = Query(default=None),
    result: str | None = Query(default=None),
    from_: str | None = Query(default=None, alias="from"),
    to: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(OpsActionAudit)
    if action:
        query = query.filter(OpsActionAudit.action == str(action).strip())
    if correlation_id:
        query = query.filter(OpsActionAudit.correlation_id == str(correlation_id).strip())
    if result:
        query = query.filter(OpsActionAudit.result == str(result).strip().upper())
    if from_:
        query = query.filter(
            OpsActionAudit.created_at >= _parse_iso_datetime_utc(from_, field_name="from")
        )
    if to:
        query = query.filter(
            OpsActionAudit.created_at <= _parse_iso_datetime_utc(to, field_name="to")
        )

    rows = (
        query.order_by(OpsActionAudit.created_at.desc(), OpsActionAudit.id.desc())
        .limit(2000)
        .all()
    )

    filtered: list[OpsActionAudit] = []
    for row in rows:
        details = row.details_json if isinstance(row.details_json, dict) else {}
        row_partner_id = _extract_partner_id(details)
        if partner_id and str(row_partner_id or "").strip() != str(partner_id).strip():
            continue
        filtered.append(row)

    sliced = filtered[offset : offset + limit]
    items = []
    for row in sliced:
        details = row.details_json if isinstance(row.details_json, dict) else {}
        row_partner_id = _extract_partner_id(details)
        items.append(
            PartnerOpsAuditItemOut(
                id=row.id,
                action=row.action,
                result=row.result,
                correlation_id=row.correlation_id,
                user_id=row.user_id,
                role=row.role,
                partner_id=(str(row_partner_id) if row_partner_id else None),
                error_message=row.error_message,
                details=details,
                created_at=_to_iso_utc(row.created_at),
            )
        )

    return PartnerOpsAuditListOut(
        ok=True,
        total=len(filtered),
        limit=limit,
        offset=offset,
        items=items,
    )


@router.get("/ops/audit/actions", response_model=PartnerOpsActionsOut)
def get_partners_ops_audit_actions(
    from_: str | None = Query(default=None, alias="from"),
    to: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(OpsActionAudit)
    if from_:
        query = query.filter(
            OpsActionAudit.created_at >= _parse_iso_datetime_utc(from_, field_name="from")
        )
    if to:
        query = query.filter(
            OpsActionAudit.created_at <= _parse_iso_datetime_utc(to, field_name="to")
        )
    rows = query.order_by(OpsActionAudit.action.asc()).limit(5000).all()
    actions = sorted({row.action for row in rows if row.action})
    return PartnerOpsActionsOut(ok=True, total=len(actions), actions=actions)


@router.get("/ops/audit/kpis", response_model=PartnerOpsKpisOut)
def get_partners_ops_audit_kpis(
    from_: str | None = Query(default=None, alias="from"),
    to: str | None = Query(default=None),
    partner_id: str | None = Query(default=None),
    top_partners_limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    now_utc = datetime.now(timezone.utc)
    window_to = _parse_iso_datetime_utc(to, field_name="to") if to else now_utc
    window_from = (
        _parse_iso_datetime_utc(from_, field_name="from")
        if from_
        else (window_to - timedelta(days=7))
    )
    if window_from > window_to:
        raise HTTPException(
            status_code=422,
            detail={"type": "INVALID_DATE_RANGE", "message": "from deve ser menor ou igual a to."},
        )

    rows_raw = (
        db.query(OpsActionAudit)
        .filter(
            OpsActionAudit.created_at >= window_from,
            OpsActionAudit.created_at <= window_to,
        )
        .order_by(OpsActionAudit.created_at.desc(), OpsActionAudit.id.desc())
        .limit(10000)
        .all()
    )
    rows: list[OpsActionAudit] = []
    for row in rows_raw:
        if not partner_id:
            rows.append(row)
            continue
        details = row.details_json if isinstance(row.details_json, dict) else {}
        if _extract_partner_id(details) == str(partner_id).strip():
            rows.append(row)

    action_counter: Counter[str] = Counter()
    result_counter: Counter[str] = Counter()
    error_daily_counter: Counter[str] = Counter()
    partner_counter: Counter[str] = Counter()
    total_errors = 0

    for row in rows:
        action = str(row.action or "").strip()
        result = str(row.result or "").strip().upper()
        if action:
            action_counter[action] += 1
        if result:
            result_counter[result] += 1
        if result == "ERROR":
            total_errors += 1
            day_key = _to_iso_utc(row.created_at)[:10]
            error_daily_counter[day_key] += 1

        details = row.details_json if isinstance(row.details_json, dict) else {}
        row_partner_id = _extract_partner_id(details)
        if row_partner_id:
            partner_counter[row_partner_id] += 1

    total_events = len(rows)
    error_rate_pct = round((total_errors / total_events) * 100, 2) if total_events > 0 else 0.0

    counts_by_action = [
        PartnerOpsKpiCountOut(key=key, count=count)
        for key, count in action_counter.most_common()
    ]
    counts_by_result = [
        PartnerOpsKpiCountOut(key=key, count=count)
        for key, count in result_counter.most_common()
    ]
    errors_by_day = [
        PartnerOpsKpiErrorDailyOut(day=day, count=error_daily_counter[day])
        for day in sorted(error_daily_counter.keys())
    ]
    top_partners = [
        PartnerOpsKpiTopPartnerOut(partner_id=partner_id, count=count)
        for partner_id, count in partner_counter.most_common(top_partners_limit)
    ]

    return PartnerOpsKpisOut(
        ok=True,
        **{
            "from": _to_iso_utc(window_from),
            "to": _to_iso_utc(window_to),
        },
        total_events=total_events,
        total_errors=total_errors,
        error_rate_pct=error_rate_pct,
        counts_by_action=counts_by_action,
        counts_by_result=counts_by_result,
        errors_by_day=errors_by_day,
        top_partners=top_partners,
    )


@router.get("/ops/audit/changes-series", response_model=PartnerOpsChangesSeriesOut)
def get_partners_ops_changes_series(
    from_: str | None = Query(default=None, alias="from"),
    to: str | None = Query(default=None),
    partner_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    now_utc = datetime.now(timezone.utc)
    window_to = _parse_iso_datetime_utc(to, field_name="to") if to else now_utc
    window_from = (
        _parse_iso_datetime_utc(from_, field_name="from")
        if from_
        else (window_to - timedelta(days=7))
    )
    if window_from > window_to:
        raise HTTPException(
            status_code=422,
            detail={"type": "INVALID_DATE_RANGE", "message": "from deve ser menor ou igual a to."},
        )

    rows_raw = (
        db.query(OpsActionAudit)
        .filter(
            OpsActionAudit.created_at >= window_from,
            OpsActionAudit.created_at <= window_to,
        )
        .order_by(OpsActionAudit.created_at.asc(), OpsActionAudit.id.asc())
        .limit(10000)
        .all()
    )
    rows: list[OpsActionAudit] = []
    for row in rows_raw:
        if not partner_id:
            rows.append(row)
            continue
        details = row.details_json if isinstance(row.details_json, dict) else {}
        if _extract_partner_id(details) == str(partner_id).strip():
            rows.append(row)

    daily_accumulator: dict[str, dict[str, int]] = {}
    distribution_counter: Counter[str] = Counter()

    for row in rows:
        day_key = _to_iso_utc(row.created_at)[:10]
        change_type = _resolve_change_type(row.action)
        distribution_counter[change_type] += 1

        if day_key not in daily_accumulator:
            daily_accumulator[day_key] = {
                "total": 0,
                "status": 0,
                "contact": 0,
                "sla": 0,
                "other": 0,
            }
        daily_accumulator[day_key]["total"] += 1
        daily_accumulator[day_key][change_type] += 1

    daily_series = [
        PartnerOpsChangeDailyOut(
            day=day,
            total=values["total"],
            status=values["status"],
            contact=values["contact"],
            sla=values["sla"],
            other=values["other"],
        )
        for day, values in sorted(daily_accumulator.items(), key=lambda item: item[0])
    ]

    total_changes = len(rows)
    distribution = []
    for key in ("status", "contact", "sla", "other"):
        count = int(distribution_counter.get(key, 0))
        pct = round((count / total_changes) * 100, 2) if total_changes > 0 else 0.0
        distribution.append(
            PartnerOpsChangeDistributionItemOut(
                change_type=key,
                count=count,
                pct=pct,
            )
        )

    badges = [
        PartnerOpsBadgeLegendItemOut(key="status", label="Status", color="#2563EB", icon="sync"),
        PartnerOpsBadgeLegendItemOut(key="contact", label="Contact", color="#0F766E", icon="users"),
        PartnerOpsBadgeLegendItemOut(key="sla", label="SLA", color="#7C3AED", icon="timer"),
        PartnerOpsBadgeLegendItemOut(key="other", label="Other", color="#64748B", icon="dots"),
    ]

    return PartnerOpsChangesSeriesOut(
        ok=True,
        **{"from": _to_iso_utc(window_from), "to": _to_iso_utc(window_to)},
        total_changes=total_changes,
        daily_series=daily_series,
        distribution=distribution,
        badges=badges,
    )


@router.get("/ops/audit/compare", response_model=PartnerOpsCompareOut)
def get_partners_ops_audit_compare(
    from_: str | None = Query(default=None, alias="from"),
    to: str | None = Query(default=None),
    partner_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    now_utc = datetime.now(timezone.utc)
    current_to = _parse_iso_datetime_utc(to, field_name="to") if to else now_utc
    current_from = (
        _parse_iso_datetime_utc(from_, field_name="from")
        if from_
        else (current_to - timedelta(days=7))
    )
    if current_from > current_to:
        raise HTTPException(
            status_code=422,
            detail={"type": "INVALID_DATE_RANGE", "message": "from deve ser menor ou igual a to."},
        )

    window_span = current_to - current_from
    previous_to = current_from
    previous_from = previous_to - window_span

    current_rows_raw = (
        db.query(OpsActionAudit)
        .filter(
            OpsActionAudit.created_at >= current_from,
            OpsActionAudit.created_at <= current_to,
        )
        .order_by(OpsActionAudit.created_at.desc(), OpsActionAudit.id.desc())
        .limit(10000)
        .all()
    )
    previous_rows_raw = (
        db.query(OpsActionAudit)
        .filter(
            OpsActionAudit.created_at >= previous_from,
            OpsActionAudit.created_at <= previous_to,
        )
        .order_by(OpsActionAudit.created_at.desc(), OpsActionAudit.id.desc())
        .limit(10000)
        .all()
    )
    current_rows: list[OpsActionAudit] = []
    for row in current_rows_raw:
        if not partner_id:
            current_rows.append(row)
            continue
        details = row.details_json if isinstance(row.details_json, dict) else {}
        if _extract_partner_id(details) == str(partner_id).strip():
            current_rows.append(row)

    previous_rows: list[OpsActionAudit] = []
    for row in previous_rows_raw:
        if not partner_id:
            previous_rows.append(row)
            continue
        details = row.details_json if isinstance(row.details_json, dict) else {}
        if _extract_partner_id(details) == str(partner_id).strip():
            previous_rows.append(row)

    current_counter = _collect_change_type_counter(current_rows)
    previous_counter = _collect_change_type_counter(previous_rows)

    label_map = {
        "status": "Status",
        "contact": "Contact",
        "sla": "SLA",
        "other": "Other",
    }
    badge_bg_map = {
        "status": "#DBEAFE",
        "contact": "#CCFBF1",
        "sla": "#EDE9FE",
        "other": "#E2E8F0",
    }
    badge_text_map = {
        "status": "#1D4ED8",
        "contact": "#0F766E",
        "sla": "#6D28D9",
        "other": "#334155",
    }

    cards: list[PartnerOpsCompareCardOut] = []
    for change_type in ("status", "contact", "sla", "other"):
        current_count = int(current_counter.get(change_type, 0))
        previous_count = int(previous_counter.get(change_type, 0))
        delta_count = current_count - previous_count
        delta_pct = _safe_delta_pct(current_count, previous_count)
        trend = "stable"
        if delta_count > 0:
            trend = "up"
        elif delta_count < 0:
            trend = "down"
        cards.append(
            PartnerOpsCompareCardOut(
                change_type=change_type,
                label=label_map[change_type],
                current_count=current_count,
                previous_count=previous_count,
                delta_count=delta_count,
                delta_pct=delta_pct,
                trend=trend,
                badge_bg_color=badge_bg_map[change_type],
                badge_text_color=badge_text_map[change_type],
            )
        )

    total_current = len(current_rows)
    total_previous = len(previous_rows)
    total_delta_count = total_current - total_previous
    total_delta_pct = _safe_delta_pct(total_current, total_previous)
    confidence_level, volume_note = _resolve_confidence_and_note(
        total_current=total_current,
        total_previous=total_previous,
    )
    confidence_badge = _resolve_confidence_badge(confidence_level)
    data_quality_flags = _build_data_quality_flags(
        total_current=total_current,
        total_previous=total_previous,
    )

    badges = [
        PartnerOpsBadgeLegendItemOut(key="status", label="Status", color="#2563EB", icon="sync"),
        PartnerOpsBadgeLegendItemOut(key="contact", label="Contact", color="#0F766E", icon="users"),
        PartnerOpsBadgeLegendItemOut(key="sla", label="SLA", color="#7C3AED", icon="timer"),
        PartnerOpsBadgeLegendItemOut(key="other", label="Other", color="#64748B", icon="dots"),
        PartnerOpsBadgeLegendItemOut(key="trend_up", label="Crescimento", color="#16A34A", icon="trending-up"),
        PartnerOpsBadgeLegendItemOut(key="trend_down", label="Queda", color="#DC2626", icon="trending-down"),
        PartnerOpsBadgeLegendItemOut(key="trend_stable", label="Estável", color="#475569", icon="minus"),
    ]

    return PartnerOpsCompareOut(
        ok=True,
        **{
            "from": _to_iso_utc(current_from),
            "to": _to_iso_utc(current_to),
        },
        previous_from=_to_iso_utc(previous_from),
        previous_to=_to_iso_utc(previous_to),
        total_current=total_current,
        total_previous=total_previous,
        total_delta_count=total_delta_count,
        total_delta_pct=total_delta_pct,
        confidence_level=confidence_level,
        volume_note=volume_note,
        confidence_badge=confidence_badge,
        data_quality_flags=data_quality_flags,
        cards=cards,
        badges=badges,
    )


@router.get("/ops/dashboard", response_model=PartnerOpsDashboardOut)
def get_partners_ops_dashboard(
    from_: str | None = Query(default=None, alias="from"),
    to: str | None = Query(default=None),
    partner_id: str | None = Query(default=None),
    include_sections: str | None = Query(default=None, description="Ex.: kpis,compare,changes_series"),
    top_partners_limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    now_utc = datetime.now(timezone.utc)
    window_to = _parse_iso_datetime_utc(to, field_name="to") if to else now_utc
    window_from = (
        _parse_iso_datetime_utc(from_, field_name="from")
        if from_
        else (window_to - timedelta(days=7))
    )
    if window_from > window_to:
        raise HTTPException(
            status_code=422,
            detail={"type": "INVALID_DATE_RANGE", "message": "from deve ser menor ou igual a to."},
        )

    sections = _parse_include_sections(include_sections)
    kpis = None
    compare = None
    changes_series = None

    # Reutiliza a mesma lógica já validada pelos endpoints especializados.
    if "kpis" in sections:
        kpis = get_partners_ops_audit_kpis(
            from_=window_from.isoformat(),
            to=window_to.isoformat(),
            partner_id=partner_id,
            top_partners_limit=top_partners_limit,
            db=db,
        )
    if "compare" in sections:
        compare = get_partners_ops_audit_compare(
            from_=window_from.isoformat(),
            to=window_to.isoformat(),
            partner_id=partner_id,
            db=db,
        )
    if "changes_series" in sections:
        changes_series = get_partners_ops_changes_series(
            from_=window_from.isoformat(),
            to=window_to.isoformat(),
            partner_id=partner_id,
            db=db,
        )

    return PartnerOpsDashboardOut(
        ok=True,
        **{"from": _to_iso_utc(window_from), "to": _to_iso_utc(window_to)},
        timezone_ref="UTC",
        partner_id=(str(partner_id).strip() if partner_id else None),
        included_sections=sections,
        kpis=kpis,
        compare=compare,
        changes_series=changes_series,
    )


@router.get("/ops/dashboard/view", response_class=HTMLResponse)
def get_partners_ops_dashboard_view() -> HTMLResponse:
    html = """
<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <title>ELLAN LAB OPS Dashboard</title>
    <style>
      body { font-family: Inter, Arial, sans-serif; margin: 24px; background:#F8FAFC; color:#0F172A; }
      h1 { margin: 0 0 16px 0; font-size: 24px; }
      .row { display:flex; gap:12px; flex-wrap:wrap; margin-bottom: 12px; }
      input, select, button { padding:8px 10px; border:1px solid #CBD5E1; border-radius:8px; background:#fff; }
      button { background:#0F766E; color:#fff; border:none; cursor:pointer; }
      .cards { display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap:12px; margin: 16px 0; }
      .card { background:#fff; border:1px solid #E2E8F0; border-radius:12px; padding:12px; }
      .label { color:#475569; font-size:12px; text-transform: uppercase; letter-spacing: .04em; }
      .value { font-size:26px; font-weight:700; margin-top:6px; }
      pre { background:#0B1220; color:#E2E8F0; border-radius:12px; padding:12px; overflow:auto; font-size:12px; }
      .muted { color:#64748B; font-size:12px; }
    </style>
  </head>
  <body>
    <h1>OPS Dashboard (Partners)</h1>
    <div class="row">
      <input id="from" placeholder="from (ISO-8601 opcional)" size="30" />
      <input id="to" placeholder="to (ISO-8601 opcional)" size="30" />
      <input id="partnerId" placeholder="partner_id (opcional)" size="28" />
      <input id="sections" value="kpis,compare,changes_series" size="28" />
      <button onclick="loadData()">Atualizar</button>
    </div>
    <div class="muted">Exemplo sections: kpis,compare | compare | changes_series</div>
    <div class="cards">
      <div class="card"><div class="label">Total Eventos</div><div id="totalEvents" class="value">-</div></div>
      <div class="card"><div class="label">Erro %</div><div id="errorRate" class="value">-</div></div>
      <div class="card"><div class="label">Delta Total %</div><div id="deltaPct" class="value">-</div></div>
      <div class="card"><div class="label">Confianca</div><div id="confidence" class="value">-</div></div>
    </div>
    <pre id="payload">Carregando...</pre>
    <script>
      async function loadData() {
        const params = new URLSearchParams();
        const from = document.getElementById('from').value.trim();
        const to = document.getElementById('to').value.trim();
        const partnerId = document.getElementById('partnerId').value.trim();
        const sections = document.getElementById('sections').value.trim();
        if (from) params.set('from', from);
        if (to) params.set('to', to);
        if (partnerId) params.set('partner_id', partnerId);
        if (sections) params.set('include_sections', sections);
        const url = '/partners/ops/dashboard?' + params.toString();
        const resp = await fetch(url);
        const data = await resp.json();
        document.getElementById('payload').textContent = JSON.stringify(data, null, 2);
        document.getElementById('totalEvents').textContent = data?.kpis?.total_events ?? '-';
        document.getElementById('errorRate').textContent = (data?.kpis?.error_rate_pct ?? '-') + (data?.kpis ? '%' : '');
        document.getElementById('deltaPct').textContent = (data?.compare?.total_delta_pct ?? '-') + (data?.compare ? '%' : '');
        document.getElementById('confidence').textContent = data?.compare?.confidence_level ?? '-';
      }
      loadData();
    </script>
  </body>
</html>
"""
    return HTMLResponse(content=html)


@router.patch("/ecommerce/{partner_id}/status", response_model=PartnerStatusOut)
def patch_ecommerce_partner_status(
    partner_id: str,
    payload: PartnerStatusTransitionIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    to_status = str(payload.to_status or "").strip().upper()
    if to_status not in _PARTNER_STATUSES:
        raise HTTPException(
            status_code=422,
            detail={
                "type": "INVALID_PARTNER_STATUS",
                "message": "Status inválido para parceiro.",
                "allowed_statuses": sorted(_PARTNER_STATUSES),
            },
        )

    from_status = _load_partner_status(db, partner_id=partner_id)
    if from_status == to_status:
        raise HTTPException(
            status_code=409,
            detail={
                "type": "STATUS_UNCHANGED",
                "message": "O parceiro já está nesse status.",
                "status": to_status,
            },
        )

    allowed_targets = _ALLOWED_TRANSITIONS.get(from_status, set())
    if to_status not in allowed_targets:
        raise HTTPException(
            status_code=422,
            detail={
                "type": "INVALID_STATUS_TRANSITION",
                "message": "Transição de status não permitida.",
                "from_status": from_status,
                "to_status": to_status,
                "allowed_targets": sorted(allowed_targets),
            },
        )

    db.execute(
        text(
            """
            UPDATE ecommerce_partners
            SET status = :status,
                updated_at = NOW()
            WHERE id = :id
            """
        ),
        {"id": partner_id, "status": to_status},
    )

    changed_at = datetime.now(timezone.utc)
    history_row = PartnerStatusHistory(
        id=str(uuid4()),
        partner_id=partner_id,
        partner_type="ECOMMERCE",
        from_status=from_status,
        to_status=to_status,
        reason=(payload.reason.strip() if payload.reason else None),
        changed_by=str(current_user.id) if current_user and current_user.id else None,
        changed_at=changed_at,
    )
    db.add(history_row)
    db.commit()

    return PartnerStatusOut(
        ok=True,
        partner_id=partner_id,
        partner_type="ECOMMERCE",
        from_status=from_status,
        to_status=to_status,
        changed_by=history_row.changed_by,
        changed_at=_to_iso_utc(changed_at),
    )


@router.get("/ecommerce/{partner_id}/status-history", response_model=PartnerStatusHistoryListOut)
def get_ecommerce_partner_status_history(
    partner_id: str,
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    _load_partner_status(db, partner_id=partner_id)

    rows = (
        db.query(PartnerStatusHistory)
        .filter(
            PartnerStatusHistory.partner_id == partner_id,
            PartnerStatusHistory.partner_type == "ECOMMERCE",
        )
        .order_by(PartnerStatusHistory.changed_at.desc(), PartnerStatusHistory.id.desc())
        .limit(limit)
        .all()
    )

    items = [
        PartnerStatusHistoryItemOut(
            id=row.id,
            partner_id=row.partner_id,
            partner_type=row.partner_type,
            from_status=row.from_status,
            to_status=row.to_status,
            reason=row.reason,
            changed_by=row.changed_by,
            changed_at=_to_iso_utc(row.changed_at),
        )
        for row in rows
    ]

    return PartnerStatusHistoryListOut(ok=True, total=len(items), items=items)


@router.get("/ecommerce/{partner_id}/contacts", response_model=PartnerContactListOut)
def get_ecommerce_partner_contacts(
    partner_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    _load_partner_status(db, partner_id=partner_id)
    rows = (
        db.query(PartnerContact)
        .filter(
            PartnerContact.partner_id == partner_id,
            PartnerContact.partner_type == "ECOMMERCE",
        )
        .order_by(PartnerContact.created_at.desc(), PartnerContact.id.desc())
        .limit(limit)
        .all()
    )
    items = [
        PartnerContactOut(
            id=row.id,
            partner_id=row.partner_id,
            partner_type=row.partner_type,
            contact_type=row.contact_type,
            name=row.name,
            email=row.email,
            phone=row.phone,
            is_primary=bool(row.is_primary),
            created_at=_to_iso_utc(row.created_at),
            updated_at=_to_iso_utc(row.updated_at),
        )
        for row in rows
    ]
    return PartnerContactListOut(ok=True, total=len(items), items=items)


@router.post("/ecommerce/{partner_id}/contacts", response_model=PartnerContactOut)
def post_ecommerce_partner_contact(
    partner_id: str,
    payload: PartnerContactIn,
    current_user: User = Depends(get_current_user),
    correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    db: Session = Depends(get_db),
):
    corr_id = _resolve_correlation_id(correlation_id)
    _load_partner_status(db, partner_id=partner_id)
    contact_type = str(payload.contact_type or "").strip().upper()
    if contact_type not in _CONTACT_TYPES:
        raise HTTPException(
            status_code=422,
            detail={
                "type": "INVALID_CONTACT_TYPE",
                "message": "Tipo de contato inválido.",
                "allowed_contact_types": sorted(_CONTACT_TYPES),
            },
        )

    if payload.is_primary:
        (
            db.query(PartnerContact)
            .filter(
                PartnerContact.partner_id == partner_id,
                PartnerContact.partner_type == "ECOMMERCE",
                PartnerContact.contact_type == contact_type,
                PartnerContact.is_primary.is_(True),
            )
            .update({"is_primary": False}, synchronize_session=False)
        )

    now = datetime.now(timezone.utc)
    row = PartnerContact(
        id=str(uuid4()),
        partner_id=partner_id,
        partner_type="ECOMMERCE",
        contact_type=contact_type,
        name=payload.name.strip(),
        email=(payload.email.strip() if payload.email else None),
        phone=(payload.phone.strip() if payload.phone else None),
        is_primary=bool(payload.is_primary),
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    _audit_ops(
        db=db,
        action="PARTNER_CONTACT_CREATE",
        result="SUCCESS",
        correlation_id=corr_id,
        user_id=str(current_user.id),
        details={
            "partner_id": partner_id,
            "partner_type": "ECOMMERCE",
            "after": {
                "id": row.id,
                "contact_type": row.contact_type,
                "name": row.name,
                "email": row.email,
                "phone": row.phone,
                "is_primary": bool(row.is_primary),
            },
        },
    )
    db.commit()

    return PartnerContactOut(
        id=row.id,
        partner_id=row.partner_id,
        partner_type=row.partner_type,
        contact_type=row.contact_type,
        name=row.name,
        email=row.email,
        phone=row.phone,
        is_primary=bool(row.is_primary),
        created_at=_to_iso_utc(row.created_at),
        updated_at=_to_iso_utc(row.updated_at),
    )


@router.put("/ecommerce/{partner_id}/contacts/{contact_id}", response_model=PartnerContactOut)
def put_ecommerce_partner_contact(
    partner_id: str,
    contact_id: str,
    payload: PartnerContactIn,
    current_user: User = Depends(get_current_user),
    correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    db: Session = Depends(get_db),
):
    corr_id = _resolve_correlation_id(correlation_id)
    _load_partner_status(db, partner_id=partner_id)
    row = db.get(PartnerContact, contact_id)
    if not row or row.partner_id != partner_id or row.partner_type != "ECOMMERCE":
        raise HTTPException(status_code=404, detail={"type": "CONTACT_NOT_FOUND", "message": "Contato não encontrado."})

    contact_type = str(payload.contact_type or "").strip().upper()
    if contact_type not in _CONTACT_TYPES:
        raise HTTPException(status_code=422, detail={"type": "INVALID_CONTACT_TYPE", "allowed_contact_types": sorted(_CONTACT_TYPES)})

    before = {
        "id": row.id,
        "contact_type": row.contact_type,
        "name": row.name,
        "email": row.email,
        "phone": row.phone,
        "is_primary": bool(row.is_primary),
    }
    if payload.is_primary:
        (
            db.query(PartnerContact)
            .filter(
                PartnerContact.partner_id == partner_id,
                PartnerContact.partner_type == "ECOMMERCE",
                PartnerContact.contact_type == contact_type,
                PartnerContact.is_primary.is_(True),
                PartnerContact.id != row.id,
            )
            .update({"is_primary": False}, synchronize_session=False)
        )

    row.contact_type = contact_type
    row.name = payload.name.strip()
    row.email = payload.email.strip() if payload.email else None
    row.phone = payload.phone.strip() if payload.phone else None
    row.is_primary = bool(payload.is_primary)
    row.updated_at = datetime.now(timezone.utc)

    _audit_ops(
        db=db,
        action="PARTNER_CONTACT_PUT",
        result="SUCCESS",
        correlation_id=corr_id,
        user_id=str(current_user.id),
        details={"partner_id": partner_id, "before": before, "after": {"id": row.id, "contact_type": row.contact_type, "name": row.name, "email": row.email, "phone": row.phone, "is_primary": bool(row.is_primary)}},
    )
    db.commit()

    return PartnerContactOut(
        id=row.id,
        partner_id=row.partner_id,
        partner_type=row.partner_type,
        contact_type=row.contact_type,
        name=row.name,
        email=row.email,
        phone=row.phone,
        is_primary=bool(row.is_primary),
        created_at=_to_iso_utc(row.created_at),
        updated_at=_to_iso_utc(row.updated_at),
    )


@router.patch("/ecommerce/{partner_id}/contacts/{contact_id}", response_model=PartnerContactOut)
def patch_ecommerce_partner_contact(
    partner_id: str,
    contact_id: str,
    payload: PartnerContactPatchIn,
    current_user: User = Depends(get_current_user),
    correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    db: Session = Depends(get_db),
):
    corr_id = _resolve_correlation_id(correlation_id)
    _load_partner_status(db, partner_id=partner_id)
    row = db.get(PartnerContact, contact_id)
    if not row or row.partner_id != partner_id or row.partner_type != "ECOMMERCE":
        raise HTTPException(status_code=404, detail={"type": "CONTACT_NOT_FOUND", "message": "Contato não encontrado."})

    before = {"id": row.id, "contact_type": row.contact_type, "name": row.name, "email": row.email, "phone": row.phone, "is_primary": bool(row.is_primary)}
    next_contact_type = row.contact_type
    if payload.contact_type is not None:
        next_contact_type = str(payload.contact_type).strip().upper()
        if next_contact_type not in _CONTACT_TYPES:
            raise HTTPException(status_code=422, detail={"type": "INVALID_CONTACT_TYPE", "allowed_contact_types": sorted(_CONTACT_TYPES)})

    next_is_primary = bool(row.is_primary if payload.is_primary is None else payload.is_primary)
    if next_is_primary:
        (
            db.query(PartnerContact)
            .filter(
                PartnerContact.partner_id == partner_id,
                PartnerContact.partner_type == "ECOMMERCE",
                PartnerContact.contact_type == next_contact_type,
                PartnerContact.is_primary.is_(True),
                PartnerContact.id != row.id,
            )
            .update({"is_primary": False}, synchronize_session=False)
        )

    row.contact_type = next_contact_type
    if payload.name is not None:
        row.name = payload.name.strip()
    if payload.email is not None:
        row.email = payload.email.strip() or None
    if payload.phone is not None:
        row.phone = payload.phone.strip() or None
    row.is_primary = next_is_primary
    row.updated_at = datetime.now(timezone.utc)

    _audit_ops(
        db=db,
        action="PARTNER_CONTACT_PATCH",
        result="SUCCESS",
        correlation_id=corr_id,
        user_id=str(current_user.id),
        details={"partner_id": partner_id, "before": before, "after": {"id": row.id, "contact_type": row.contact_type, "name": row.name, "email": row.email, "phone": row.phone, "is_primary": bool(row.is_primary)}},
    )
    db.commit()

    return PartnerContactOut(
        id=row.id,
        partner_id=row.partner_id,
        partner_type=row.partner_type,
        contact_type=row.contact_type,
        name=row.name,
        email=row.email,
        phone=row.phone,
        is_primary=bool(row.is_primary),
        created_at=_to_iso_utc(row.created_at),
        updated_at=_to_iso_utc(row.updated_at),
    )


@router.delete("/ecommerce/{partner_id}/contacts/{contact_id}", response_model=PartnerDeleteOut)
def delete_ecommerce_partner_contact(
    partner_id: str,
    contact_id: str,
    current_user: User = Depends(get_current_user),
    correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    db: Session = Depends(get_db),
):
    corr_id = _resolve_correlation_id(correlation_id)
    _load_partner_status(db, partner_id=partner_id)
    row = db.get(PartnerContact, contact_id)
    if not row or row.partner_id != partner_id or row.partner_type != "ECOMMERCE":
        raise HTTPException(status_code=404, detail={"type": "CONTACT_NOT_FOUND", "message": "Contato não encontrado."})

    before = {"id": row.id, "contact_type": row.contact_type, "name": row.name, "email": row.email, "phone": row.phone, "is_primary": bool(row.is_primary)}
    db.delete(row)
    _audit_ops(
        db=db,
        action="PARTNER_CONTACT_DELETE",
        result="SUCCESS",
        correlation_id=corr_id,
        user_id=str(current_user.id),
        details={"partner_id": partner_id, "before": before, "after": None},
    )
    db.commit()
    return PartnerDeleteOut(ok=True, id=contact_id, message="Contato removido.")


@router.get("/ecommerce/{partner_id}/sla-agreements", response_model=PartnerSlaAgreementListOut)
def get_ecommerce_partner_sla_agreements(
    partner_id: str,
    only_active: bool = Query(default=False),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    _load_partner_status(db, partner_id=partner_id)
    query = db.query(PartnerSlaAgreement).filter(
        PartnerSlaAgreement.partner_id == partner_id,
        PartnerSlaAgreement.partner_type == "ECOMMERCE",
    )
    if only_active:
        query = query.filter(PartnerSlaAgreement.is_active.is_(True))

    rows = (
        query.order_by(PartnerSlaAgreement.created_at.desc(), PartnerSlaAgreement.id.desc())
        .limit(limit)
        .all()
    )
    items = [
        PartnerSlaAgreementOut(
            id=row.id,
            partner_id=row.partner_id,
            partner_type=row.partner_type,
            country=row.country,
            product_category=row.product_category,
            sla_pickup_hours=int(row.sla_pickup_hours or 0),
            sla_return_hours=int(row.sla_return_hours or 0),
            penalty_pct=float(row.penalty_pct or Decimal("0")),
            valid_from=row.valid_from.isoformat(),
            valid_until=(row.valid_until.isoformat() if row.valid_until else None),
            is_active=bool(row.is_active),
            created_at=_to_iso_utc(row.created_at),
        )
        for row in rows
    ]
    return PartnerSlaAgreementListOut(ok=True, total=len(items), items=items)


@router.post("/ecommerce/{partner_id}/sla-agreements", response_model=PartnerSlaAgreementOut)
def post_ecommerce_partner_sla_agreement(
    partner_id: str,
    payload: PartnerSlaAgreementIn,
    current_user: User = Depends(get_current_user),
    correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    db: Session = Depends(get_db),
):
    corr_id = _resolve_correlation_id(correlation_id)
    _load_partner_status(db, partner_id=partner_id)
    valid_from = _parse_iso_date(payload.valid_from, field_name="valid_from")
    valid_until = _parse_iso_date(payload.valid_until, field_name="valid_until") if payload.valid_until else None
    if valid_until and valid_until < valid_from:
        raise HTTPException(
            status_code=422,
            detail={
                "type": "INVALID_DATE_RANGE",
                "message": "valid_until deve ser maior ou igual a valid_from.",
            },
        )

    row = PartnerSlaAgreement(
        id=str(uuid4()),
        partner_id=partner_id,
        partner_type="ECOMMERCE",
        country=(payload.country or "BR").strip().upper(),
        product_category=(payload.product_category.strip() if payload.product_category else None),
        sla_pickup_hours=int(payload.sla_pickup_hours),
        sla_return_hours=int(payload.sla_return_hours),
        penalty_pct=payload.penalty_pct,
        valid_from=valid_from,
        valid_until=valid_until,
        is_active=bool(payload.is_active),
        created_at=datetime.now(timezone.utc),
    )
    db.add(row)
    _audit_ops(
        db=db,
        action="PARTNER_SLA_CREATE",
        result="SUCCESS",
        correlation_id=corr_id,
        user_id=str(current_user.id),
        details={
            "partner_id": partner_id,
            "after": {
                "id": row.id,
                "country": row.country,
                "product_category": row.product_category,
                "sla_pickup_hours": int(row.sla_pickup_hours),
                "sla_return_hours": int(row.sla_return_hours),
                "penalty_pct": float(row.penalty_pct or Decimal("0")),
                "valid_from": row.valid_from.isoformat(),
                "valid_until": (row.valid_until.isoformat() if row.valid_until else None),
                "is_active": bool(row.is_active),
            },
        },
    )
    db.commit()

    return PartnerSlaAgreementOut(
        id=row.id,
        partner_id=row.partner_id,
        partner_type=row.partner_type,
        country=row.country,
        product_category=row.product_category,
        sla_pickup_hours=int(row.sla_pickup_hours),
        sla_return_hours=int(row.sla_return_hours),
        penalty_pct=float(row.penalty_pct or Decimal("0")),
        valid_from=row.valid_from.isoformat(),
        valid_until=(row.valid_until.isoformat() if row.valid_until else None),
        is_active=bool(row.is_active),
        created_at=_to_iso_utc(row.created_at),
    )


@router.put("/ecommerce/{partner_id}/sla-agreements/{agreement_id}", response_model=PartnerSlaAgreementOut)
def put_ecommerce_partner_sla_agreement(
    partner_id: str,
    agreement_id: str,
    payload: PartnerSlaAgreementIn,
    current_user: User = Depends(get_current_user),
    correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    db: Session = Depends(get_db),
):
    corr_id = _resolve_correlation_id(correlation_id)
    _load_partner_status(db, partner_id=partner_id)
    row = db.get(PartnerSlaAgreement, agreement_id)
    if not row or row.partner_id != partner_id or row.partner_type != "ECOMMERCE":
        raise HTTPException(status_code=404, detail={"type": "SLA_NOT_FOUND", "message": "SLA agreement não encontrado."})

    valid_from = _parse_iso_date(payload.valid_from, field_name="valid_from")
    valid_until = _parse_iso_date(payload.valid_until, field_name="valid_until") if payload.valid_until else None
    if valid_until and valid_until < valid_from:
        raise HTTPException(status_code=422, detail={"type": "INVALID_DATE_RANGE", "message": "valid_until deve ser maior ou igual a valid_from."})

    before = {
        "id": row.id,
        "country": row.country,
        "product_category": row.product_category,
        "sla_pickup_hours": int(row.sla_pickup_hours),
        "sla_return_hours": int(row.sla_return_hours),
        "penalty_pct": float(row.penalty_pct or Decimal("0")),
        "valid_from": row.valid_from.isoformat(),
        "valid_until": (row.valid_until.isoformat() if row.valid_until else None),
        "is_active": bool(row.is_active),
    }
    row.country = (payload.country or "BR").strip().upper()
    row.product_category = payload.product_category.strip() if payload.product_category else None
    row.sla_pickup_hours = int(payload.sla_pickup_hours)
    row.sla_return_hours = int(payload.sla_return_hours)
    row.penalty_pct = payload.penalty_pct
    row.valid_from = valid_from
    row.valid_until = valid_until
    row.is_active = bool(payload.is_active)

    _audit_ops(
        db=db,
        action="PARTNER_SLA_PUT",
        result="SUCCESS",
        correlation_id=corr_id,
        user_id=str(current_user.id),
        details={"partner_id": partner_id, "before": before, "after": {"id": row.id, "country": row.country, "product_category": row.product_category, "sla_pickup_hours": int(row.sla_pickup_hours), "sla_return_hours": int(row.sla_return_hours), "penalty_pct": float(row.penalty_pct or Decimal('0')), "valid_from": row.valid_from.isoformat(), "valid_until": (row.valid_until.isoformat() if row.valid_until else None), "is_active": bool(row.is_active)}},
    )
    db.commit()

    return PartnerSlaAgreementOut(
        id=row.id,
        partner_id=row.partner_id,
        partner_type=row.partner_type,
        country=row.country,
        product_category=row.product_category,
        sla_pickup_hours=int(row.sla_pickup_hours),
        sla_return_hours=int(row.sla_return_hours),
        penalty_pct=float(row.penalty_pct or Decimal("0")),
        valid_from=row.valid_from.isoformat(),
        valid_until=(row.valid_until.isoformat() if row.valid_until else None),
        is_active=bool(row.is_active),
        created_at=_to_iso_utc(row.created_at),
    )


@router.patch("/ecommerce/{partner_id}/sla-agreements/{agreement_id}", response_model=PartnerSlaAgreementOut)
def patch_ecommerce_partner_sla_agreement(
    partner_id: str,
    agreement_id: str,
    payload: PartnerSlaAgreementPatchIn,
    current_user: User = Depends(get_current_user),
    correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    db: Session = Depends(get_db),
):
    corr_id = _resolve_correlation_id(correlation_id)
    _load_partner_status(db, partner_id=partner_id)
    row = db.get(PartnerSlaAgreement, agreement_id)
    if not row or row.partner_id != partner_id or row.partner_type != "ECOMMERCE":
        raise HTTPException(status_code=404, detail={"type": "SLA_NOT_FOUND", "message": "SLA agreement não encontrado."})

    before = {"id": row.id, "country": row.country, "product_category": row.product_category, "sla_pickup_hours": int(row.sla_pickup_hours), "sla_return_hours": int(row.sla_return_hours), "penalty_pct": float(row.penalty_pct or Decimal("0")), "valid_from": row.valid_from.isoformat(), "valid_until": (row.valid_until.isoformat() if row.valid_until else None), "is_active": bool(row.is_active)}

    if payload.country is not None:
        row.country = payload.country.strip().upper()
    if payload.product_category is not None:
        row.product_category = payload.product_category.strip() or None
    if payload.sla_pickup_hours is not None:
        row.sla_pickup_hours = int(payload.sla_pickup_hours)
    if payload.sla_return_hours is not None:
        row.sla_return_hours = int(payload.sla_return_hours)
    if payload.penalty_pct is not None:
        row.penalty_pct = payload.penalty_pct
    if payload.valid_from is not None:
        row.valid_from = _parse_iso_date(payload.valid_from, field_name="valid_from")
    if payload.valid_until is not None:
        row.valid_until = _parse_iso_date(payload.valid_until, field_name="valid_until")
    if row.valid_until and row.valid_until < row.valid_from:
        raise HTTPException(status_code=422, detail={"type": "INVALID_DATE_RANGE", "message": "valid_until deve ser maior ou igual a valid_from."})
    if payload.is_active is not None:
        row.is_active = bool(payload.is_active)

    _audit_ops(
        db=db,
        action="PARTNER_SLA_PATCH",
        result="SUCCESS",
        correlation_id=corr_id,
        user_id=str(current_user.id),
        details={"partner_id": partner_id, "before": before, "after": {"id": row.id, "country": row.country, "product_category": row.product_category, "sla_pickup_hours": int(row.sla_pickup_hours), "sla_return_hours": int(row.sla_return_hours), "penalty_pct": float(row.penalty_pct or Decimal('0')), "valid_from": row.valid_from.isoformat(), "valid_until": (row.valid_until.isoformat() if row.valid_until else None), "is_active": bool(row.is_active)}},
    )
    db.commit()

    return PartnerSlaAgreementOut(
        id=row.id,
        partner_id=row.partner_id,
        partner_type=row.partner_type,
        country=row.country,
        product_category=row.product_category,
        sla_pickup_hours=int(row.sla_pickup_hours),
        sla_return_hours=int(row.sla_return_hours),
        penalty_pct=float(row.penalty_pct or Decimal("0")),
        valid_from=row.valid_from.isoformat(),
        valid_until=(row.valid_until.isoformat() if row.valid_until else None),
        is_active=bool(row.is_active),
        created_at=_to_iso_utc(row.created_at),
    )


@router.delete("/ecommerce/{partner_id}/sla-agreements/{agreement_id}", response_model=PartnerDeleteOut)
def delete_ecommerce_partner_sla_agreement(
    partner_id: str,
    agreement_id: str,
    current_user: User = Depends(get_current_user),
    correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    db: Session = Depends(get_db),
):
    corr_id = _resolve_correlation_id(correlation_id)
    _load_partner_status(db, partner_id=partner_id)
    row = db.get(PartnerSlaAgreement, agreement_id)
    if not row or row.partner_id != partner_id or row.partner_type != "ECOMMERCE":
        raise HTTPException(status_code=404, detail={"type": "SLA_NOT_FOUND", "message": "SLA agreement não encontrado."})

    before = {"id": row.id, "country": row.country, "product_category": row.product_category, "sla_pickup_hours": int(row.sla_pickup_hours), "sla_return_hours": int(row.sla_return_hours), "penalty_pct": float(row.penalty_pct or Decimal("0")), "valid_from": row.valid_from.isoformat(), "valid_until": (row.valid_until.isoformat() if row.valid_until else None), "is_active": bool(row.is_active)}
    db.delete(row)
    _audit_ops(
        db=db,
        action="PARTNER_SLA_DELETE",
        result="SUCCESS",
        correlation_id=corr_id,
        user_id=str(current_user.id),
        details={"partner_id": partner_id, "before": before, "after": None},
    )
    db.commit()
    return PartnerDeleteOut(ok=True, id=agreement_id, message="SLA agreement removido.")
