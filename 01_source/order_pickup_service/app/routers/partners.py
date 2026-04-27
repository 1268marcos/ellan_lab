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
    PartnerPerformanceListOut,
    PartnerPerformanceOut,
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
    PartnerSettlementApproveIn,
    PartnerSettlementPayIn,
    PartnerSettlementGenerateIn,
    PartnerSettlementItemListOut,
    PartnerSettlementItemOut,
    PartnerSettlementReconciliationAlertOut,
    PartnerSettlementReconciliationAlertTimelineItemOut,
    PartnerSettlementReconciliationAlertTimelineOut,
    PartnerSettlementReconciliationBatchRunItemOut,
    PartnerSettlementReconciliationBatchRunOut,
    PartnerSettlementReconciliationCompareOut,
    PartnerSettlementReconciliationCompareWindowOut,
    PartnerSettlementReconciliationTopDivergenceItemOut,
    PartnerSettlementReconciliationTopDivergenceSeverityCountsOut,
    PartnerSettlementReconciliationTopDivergencesOut,
    PartnerSettlementReconciliationOut,
    PartnerSettlementListOut,
    PartnerSettlementOut,
    PartnerServiceAreaIn,
    PartnerServiceAreaListOut,
    PartnerServiceAreaOut,
    PartnerEligibleProductItemOut,
    PartnerEligibleProductListOut,
    PartnerSlotAllocationPickIn,
    PartnerSlotAllocationPickOut,
    PartnerSlotAllocationPickupConfirmIn,
    PartnerSlotAllocationPickupConfirmOut,
    PartnerProductCreateIn,
    PartnerProductCreateOut,
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
    PartnerWebhookOpsAlertOut,
    PartnerWebhookOpsDailyOut,
    PartnerWebhookOpsMetricsOut,
    PartnerWebhookOpsTopEndpointOut,
    PartnerWebhookOpsTopPartnerOut,
    PartnerPickupConfirmMetricsCompareOut,
    PartnerPickupConfirmMetricsCompareWindowOut,
    PartnerPickupConfirmMetricsOut,
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


def _ensure_partner_is_active_for_catalog(db: Session, partner_id: str) -> None:
    status = str(_load_partner_status(db, partner_id=partner_id) or "DRAFT").strip().upper()
    if status != "ACTIVE":
        raise HTTPException(
            status_code=409,
            detail={
                "type": "PARTNER_NOT_ACTIVE",
                "message": "Parceiro precisa estar ACTIVE para cadastrar produtos.",
                "partner_id": partner_id,
                "status": status,
            },
        )


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


# Divergência batch vs itens: severidade para comitê (gross pesa mais que contagem isolada).
_SHARE_DIVERGENCE_MEDIUM_THRESHOLD_CENTS = 10


def _settlement_reconciliation_severity(
    *, delta_total_orders: int, delta_gross_revenue_cents: int, delta_revenue_share_cents: int
) -> str:
    abs_g = abs(int(delta_gross_revenue_cents))
    abs_o = abs(int(delta_total_orders))
    abs_s = abs(int(delta_revenue_share_cents))
    if abs_g > 0:
        return "HIGH"
    if abs_o > 0 or abs_s >= _SHARE_DIVERGENCE_MEDIUM_THRESHOLD_CENTS:
        return "MEDIUM"
    if abs_s > 0:
        return "LOW"
    return "MEDIUM"


_SETTLEMENT_SEVERITY_RANK = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}


def _parse_min_settlement_severity(min_severity: str | None) -> str | None:
    raw = str(min_severity or "").strip().upper()
    if not raw:
        return None
    if raw not in _SETTLEMENT_SEVERITY_RANK:
        raise HTTPException(
            status_code=422,
            detail={
                "type": "INVALID_MIN_SEVERITY",
                "message": "min_severity deve ser HIGH, MEDIUM ou LOW.",
                "allowed": ["HIGH", "MEDIUM", "LOW"],
            },
        )
    return raw


def _settlement_severity_meets_minimum(*, severity: str, min_severity: str | None) -> bool:
    if min_severity is None:
        return True
    return int(_SETTLEMENT_SEVERITY_RANK.get(str(severity).upper(), 0)) >= int(
        _SETTLEMENT_SEVERITY_RANK[min_severity]
    )


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


def _load_ops_audit_rows_for_compare(
    db: Session,
    *,
    window_from: datetime,
    window_to: datetime,
    partner_id: str | None,
    sort_order: str,
    max_rows: int = 10000,
) -> list[OpsActionAudit]:
    normalized_partner = str(partner_id or "").strip()
    ordering_desc = str(sort_order).lower() != "asc"
    page_size = 1000
    offset = 0
    rows: list[OpsActionAudit] = []

    while len(rows) < max_rows:
        query = (
            db.query(OpsActionAudit)
            .filter(
                OpsActionAudit.created_at >= window_from,
                OpsActionAudit.created_at <= window_to,
            )
        )
        if ordering_desc:
            query = query.order_by(OpsActionAudit.created_at.desc(), OpsActionAudit.id.desc())
        else:
            query = query.order_by(OpsActionAudit.created_at.asc(), OpsActionAudit.id.asc())

        chunk = query.offset(offset).limit(page_size).all()
        if not chunk:
            break

        if not normalized_partner:
            rows.extend(chunk)
        else:
            for row in chunk:
                details = row.details_json if isinstance(row.details_json, dict) else {}
                if _extract_partner_id(details) == normalized_partner:
                    rows.append(row)
                    if len(rows) >= max_rows:
                        break

        offset += page_size
        if len(chunk) < page_size:
            break

    return rows[:max_rows]


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


@router.get("/{partner_id}/settlements", response_model=PartnerSettlementListOut)
def get_partner_settlements(
    partner_id: str,
    from_period_start: str | None = Query(default=None),
    to_period_end: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    _load_partner_status(db, partner_id=partner_id)
    query = db.execute(
        text(
            """
            SELECT
                id, partner_id, partner_type, period_start, period_end, currency,
                total_orders, gross_revenue_cents, revenue_share_pct, revenue_share_cents,
                fees_cents, net_amount_cents, status, settled_at, settlement_ref,
                notes, created_at, updated_at
            FROM partner_settlement_batches
            WHERE partner_id = :partner_id
              AND (CAST(:from_period_start AS date) IS NULL OR period_start >= CAST(:from_period_start AS date))
              AND (CAST(:to_period_end AS date) IS NULL OR period_end <= CAST(:to_period_end AS date))
              AND (:status_filter IS NULL OR status = :status_filter)
            ORDER BY period_end DESC, created_at DESC
            LIMIT :limit
            """
        ),
        {
            "partner_id": partner_id,
            "from_period_start": (str(from_period_start).strip() if from_period_start else None),
            "to_period_end": (str(to_period_end).strip() if to_period_end else None),
            "status_filter": (str(status).strip().upper() if status else None),
            "limit": int(limit),
        },
    ).mappings().all()
    items = [
        PartnerSettlementOut(
            id=str(row["id"]),
            partner_id=str(row["partner_id"]),
            partner_type=str(row["partner_type"]),
            period_start=row["period_start"].isoformat(),
            period_end=row["period_end"].isoformat(),
            currency=str(row["currency"] or "BRL"),
            total_orders=int(row["total_orders"] or 0),
            gross_revenue_cents=int(row["gross_revenue_cents"] or 0),
            revenue_share_pct=float(row["revenue_share_pct"] or 0),
            revenue_share_cents=int(row["revenue_share_cents"] or 0),
            fees_cents=int(row["fees_cents"] or 0),
            net_amount_cents=int(row["net_amount_cents"] or 0),
            status=str(row["status"]),
            settled_at=_to_iso_utc(row["settled_at"]) if row["settled_at"] else None,
            settlement_ref=str(row["settlement_ref"]) if row["settlement_ref"] else None,
            notes=str(row["notes"]) if row["notes"] else None,
            created_at=_to_iso_utc(row["created_at"]),
            updated_at=_to_iso_utc(row["updated_at"]),
        )
        for row in query
    ]
    return PartnerSettlementListOut(ok=True, total=len(items), items=items)


@router.post("/{partner_id}/settlements/generate", response_model=PartnerSettlementOut)
def post_partner_settlement_generate(
    partner_id: str,
    payload: PartnerSettlementGenerateIn,
    current_user: User = Depends(get_current_user),
    correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    db: Session = Depends(get_db),
):
    corr_id = _resolve_correlation_id(correlation_id)
    _load_partner_status(db, partner_id=partner_id)
    period_start = _parse_iso_date(payload.period_start, field_name="period_start")
    period_end = _parse_iso_date(payload.period_end, field_name="period_end")
    if period_end < period_start:
        raise HTTPException(status_code=422, detail={"type": "INVALID_DATE_RANGE", "message": "period_end deve ser >= period_start."})

    existing = db.execute(
        text(
            """
            SELECT id FROM partner_settlement_batches
            WHERE partner_id = :partner_id
              AND period_start = :period_start
              AND period_end = :period_end
              AND status IN ('DRAFT', 'APPROVED', 'PAID')
            ORDER BY created_at DESC
            LIMIT 1
            """
        ),
        {"partner_id": partner_id, "period_start": period_start, "period_end": period_end},
    ).mappings().first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail={
                "type": "SETTLEMENT_ALREADY_EXISTS",
                "message": "Já existe batch de liquidação para esse período.",
                "batch_id": str(existing["id"]),
            },
        )

    summary = db.execute(
        text(
            """
            SELECT
                COUNT(*)::int AS total_orders,
                COALESCE(SUM(amount_cents), 0)::bigint AS gross_revenue_cents
            FROM orders
            WHERE ecommerce_partner_id = :partner_id
              AND created_at >= CAST(:period_start AS date)
              AND created_at < (CAST(:period_end AS date) + INTERVAL '1 day')
            """
        ),
        {"partner_id": partner_id, "period_start": period_start, "period_end": period_end},
    ).mappings().first() or {}
    total_orders = int(summary.get("total_orders") or 0)
    gross_revenue_cents = int(summary.get("gross_revenue_cents") or 0)
    share_pct = float(payload.revenue_share_pct)
    revenue_share_cents = int(round(gross_revenue_cents * share_pct))
    fees_cents = int(payload.fees_cents)
    net_amount_cents = int(gross_revenue_cents - revenue_share_cents - fees_cents)

    batch_id = str(uuid4())
    db.execute(
        text(
            """
            INSERT INTO partner_settlement_batches (
                id, partner_id, partner_type, period_start, period_end, currency,
                total_orders, gross_revenue_cents, revenue_share_pct, revenue_share_cents,
                fees_cents, net_amount_cents, status, notes, created_at, updated_at
            ) VALUES (
                :id, :partner_id, 'ECOMMERCE', :period_start, :period_end, :currency,
                :total_orders, :gross_revenue_cents, :revenue_share_pct, :revenue_share_cents,
                :fees_cents, :net_amount_cents, 'DRAFT', :notes, NOW(), NOW()
            )
            """
        ),
        {
            "id": batch_id,
            "partner_id": partner_id,
            "period_start": period_start,
            "period_end": period_end,
            "currency": payload.currency.strip().upper() or "BRL",
            "total_orders": total_orders,
            "gross_revenue_cents": gross_revenue_cents,
            "revenue_share_pct": Decimal(str(payload.revenue_share_pct)),
            "revenue_share_cents": revenue_share_cents,
            "fees_cents": fees_cents,
            "net_amount_cents": net_amount_cents,
            "notes": (payload.notes.strip() if payload.notes else None),
        },
    )
    db.execute(
        text(
            """
            INSERT INTO partner_settlement_items (
                batch_id, order_id, order_date, gross_cents, share_pct, share_cents, currency
            )
            SELECT
                :batch_id,
                o.id,
                o.created_at,
                o.amount_cents,
                CAST(:share_pct AS numeric(6,4)),
                ROUND(o.amount_cents * CAST(:share_pct AS numeric(6,4)))::bigint,
                :currency
            FROM orders o
            WHERE o.ecommerce_partner_id = :partner_id
              AND o.created_at >= CAST(:period_start AS date)
              AND o.created_at < (CAST(:period_end AS date) + INTERVAL '1 day')
            """
        ),
        {
            "batch_id": batch_id,
            "partner_id": partner_id,
            "period_start": period_start,
            "period_end": period_end,
            "share_pct": Decimal(str(payload.revenue_share_pct)),
            "currency": payload.currency.strip().upper() or "BRL",
        },
    )
    _audit_ops(
        db=db,
        action="PARTNER_SETTLEMENT_GENERATE",
        result="SUCCESS",
        correlation_id=corr_id,
        user_id=str(current_user.id),
        details={
            "partner_id": partner_id,
            "after": {
                "id": batch_id,
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat(),
                "total_orders": total_orders,
                "gross_revenue_cents": gross_revenue_cents,
                "revenue_share_pct": share_pct,
                "revenue_share_cents": revenue_share_cents,
                "fees_cents": fees_cents,
                "net_amount_cents": net_amount_cents,
            },
        },
    )
    db.commit()
    row = db.execute(
        text(
            """
            SELECT
                id, partner_id, partner_type, period_start, period_end, currency,
                total_orders, gross_revenue_cents, revenue_share_pct, revenue_share_cents,
                fees_cents, net_amount_cents, status, settled_at, settlement_ref,
                notes, created_at, updated_at
            FROM partner_settlement_batches
            WHERE id = :id
            """
        ),
        {"id": batch_id},
    ).mappings().first()
    return PartnerSettlementOut(
        id=str(row["id"]),
        partner_id=str(row["partner_id"]),
        partner_type=str(row["partner_type"]),
        period_start=row["period_start"].isoformat(),
        period_end=row["period_end"].isoformat(),
        currency=str(row["currency"] or "BRL"),
        total_orders=int(row["total_orders"] or 0),
        gross_revenue_cents=int(row["gross_revenue_cents"] or 0),
        revenue_share_pct=float(row["revenue_share_pct"] or 0),
        revenue_share_cents=int(row["revenue_share_cents"] or 0),
        fees_cents=int(row["fees_cents"] or 0),
        net_amount_cents=int(row["net_amount_cents"] or 0),
        status=str(row["status"]),
        settled_at=_to_iso_utc(row["settled_at"]) if row["settled_at"] else None,
        settlement_ref=str(row["settlement_ref"]) if row["settlement_ref"] else None,
        notes=str(row["notes"]) if row["notes"] else None,
        created_at=_to_iso_utc(row["created_at"]),
        updated_at=_to_iso_utc(row["updated_at"]),
    )


@router.patch("/{partner_id}/settlements/{batch_id}/approve", response_model=PartnerSettlementOut)
def patch_partner_settlement_approve(
    partner_id: str,
    batch_id: str,
    payload: PartnerSettlementApproveIn,
    current_user: User = Depends(get_current_user),
    correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    db: Session = Depends(get_db),
):
    corr_id = _resolve_correlation_id(correlation_id)
    _load_partner_status(db, partner_id=partner_id)
    before = db.execute(
        text(
            """
            SELECT id, partner_id, status, settlement_ref, notes, updated_at
            FROM partner_settlement_batches
            WHERE id = :batch_id AND partner_id = :partner_id
            """
        ),
        {"batch_id": batch_id, "partner_id": partner_id},
    ).mappings().first()
    if not before:
        raise HTTPException(status_code=404, detail={"type": "SETTLEMENT_NOT_FOUND", "message": "Batch de liquidação não encontrado."})

    if str(before["status"]) in {"APPROVED", "PAID"}:
        row = db.execute(
            text(
                """
                SELECT
                    id, partner_id, partner_type, period_start, period_end, currency,
                    total_orders, gross_revenue_cents, revenue_share_pct, revenue_share_cents,
                    fees_cents, net_amount_cents, status, settled_at, settlement_ref,
                    notes, created_at, updated_at
                FROM partner_settlement_batches
                WHERE id = :batch_id
                """
            ),
            {"batch_id": batch_id},
        ).mappings().first()
        return PartnerSettlementOut(
            id=str(row["id"]),
            partner_id=str(row["partner_id"]),
            partner_type=str(row["partner_type"]),
            period_start=row["period_start"].isoformat(),
            period_end=row["period_end"].isoformat(),
            currency=str(row["currency"] or "BRL"),
            total_orders=int(row["total_orders"] or 0),
            gross_revenue_cents=int(row["gross_revenue_cents"] or 0),
            revenue_share_pct=float(row["revenue_share_pct"] or 0),
            revenue_share_cents=int(row["revenue_share_cents"] or 0),
            fees_cents=int(row["fees_cents"] or 0),
            net_amount_cents=int(row["net_amount_cents"] or 0),
            status=str(row["status"]),
            settled_at=_to_iso_utc(row["settled_at"]) if row["settled_at"] else None,
            settlement_ref=str(row["settlement_ref"]) if row["settlement_ref"] else None,
            notes=str(row["notes"]) if row["notes"] else None,
            created_at=_to_iso_utc(row["created_at"]),
            updated_at=_to_iso_utc(row["updated_at"]),
        )

    db.execute(
        text(
            """
            UPDATE partner_settlement_batches
            SET status = 'APPROVED',
                settled_at = NOW(),
                settlement_ref = COALESCE(:settlement_ref, settlement_ref),
                notes = COALESCE(:notes, notes),
                updated_at = NOW()
            WHERE id = :batch_id
              AND partner_id = :partner_id
            """
        ),
        {
            "batch_id": batch_id,
            "partner_id": partner_id,
            "settlement_ref": (payload.settlement_ref.strip() if payload.settlement_ref else None),
            "notes": (payload.notes.strip() if payload.notes else None),
        },
    )
    _audit_ops(
        db=db,
        action="PARTNER_SETTLEMENT_APPROVE",
        result="SUCCESS",
        correlation_id=corr_id,
        user_id=str(current_user.id),
        details={
            "partner_id": partner_id,
            "before": {
                "id": str(before["id"]),
                "status": str(before["status"]),
                "settlement_ref": (str(before["settlement_ref"]) if before["settlement_ref"] else None),
            },
            "after": {
                "id": batch_id,
                "status": "APPROVED",
                "settlement_ref": (payload.settlement_ref.strip() if payload.settlement_ref else None),
            },
        },
    )
    db.commit()
    row = db.execute(
        text(
            """
            SELECT
                id, partner_id, partner_type, period_start, period_end, currency,
                total_orders, gross_revenue_cents, revenue_share_pct, revenue_share_cents,
                fees_cents, net_amount_cents, status, settled_at, settlement_ref,
                notes, created_at, updated_at
            FROM partner_settlement_batches
            WHERE id = :batch_id
            """
        ),
        {"batch_id": batch_id},
    ).mappings().first()
    return PartnerSettlementOut(
        id=str(row["id"]),
        partner_id=str(row["partner_id"]),
        partner_type=str(row["partner_type"]),
        period_start=row["period_start"].isoformat(),
        period_end=row["period_end"].isoformat(),
        currency=str(row["currency"] or "BRL"),
        total_orders=int(row["total_orders"] or 0),
        gross_revenue_cents=int(row["gross_revenue_cents"] or 0),
        revenue_share_pct=float(row["revenue_share_pct"] or 0),
        revenue_share_cents=int(row["revenue_share_cents"] or 0),
        fees_cents=int(row["fees_cents"] or 0),
        net_amount_cents=int(row["net_amount_cents"] or 0),
        status=str(row["status"]),
        settled_at=_to_iso_utc(row["settled_at"]) if row["settled_at"] else None,
        settlement_ref=str(row["settlement_ref"]) if row["settlement_ref"] else None,
        notes=str(row["notes"]) if row["notes"] else None,
        created_at=_to_iso_utc(row["created_at"]),
        updated_at=_to_iso_utc(row["updated_at"]),
    )


@router.patch("/{partner_id}/settlements/{batch_id}/pay", response_model=PartnerSettlementOut)
def patch_partner_settlement_pay(
    partner_id: str,
    batch_id: str,
    payload: PartnerSettlementPayIn,
    current_user: User = Depends(get_current_user),
    correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    db: Session = Depends(get_db),
):
    corr_id = _resolve_correlation_id(correlation_id)
    _load_partner_status(db, partner_id=partner_id)
    before = db.execute(
        text(
            """
            SELECT id, partner_id, status, settlement_ref, notes
            FROM partner_settlement_batches
            WHERE id = :batch_id AND partner_id = :partner_id
            """
        ),
        {"batch_id": batch_id, "partner_id": partner_id},
    ).mappings().first()
    if not before:
        raise HTTPException(status_code=404, detail={"type": "SETTLEMENT_NOT_FOUND", "message": "Batch de liquidação não encontrado."})

    previous_status = str(before["status"] or "")
    if previous_status == "PAID":
        row = db.execute(
            text(
                """
                SELECT
                    id, partner_id, partner_type, period_start, period_end, currency,
                    total_orders, gross_revenue_cents, revenue_share_pct, revenue_share_cents,
                    fees_cents, net_amount_cents, status, settled_at, settlement_ref,
                    notes, created_at, updated_at
                FROM partner_settlement_batches
                WHERE id = :batch_id
                """
            ),
            {"batch_id": batch_id},
        ).mappings().first()
        return PartnerSettlementOut(
            id=str(row["id"]),
            partner_id=str(row["partner_id"]),
            partner_type=str(row["partner_type"]),
            period_start=row["period_start"].isoformat(),
            period_end=row["period_end"].isoformat(),
            currency=str(row["currency"] or "BRL"),
            total_orders=int(row["total_orders"] or 0),
            gross_revenue_cents=int(row["gross_revenue_cents"] or 0),
            revenue_share_pct=float(row["revenue_share_pct"] or 0),
            revenue_share_cents=int(row["revenue_share_cents"] or 0),
            fees_cents=int(row["fees_cents"] or 0),
            net_amount_cents=int(row["net_amount_cents"] or 0),
            status=str(row["status"]),
            settled_at=_to_iso_utc(row["settled_at"]) if row["settled_at"] else None,
            settlement_ref=str(row["settlement_ref"]) if row["settlement_ref"] else None,
            notes=str(row["notes"]) if row["notes"] else None,
            created_at=_to_iso_utc(row["created_at"]),
            updated_at=_to_iso_utc(row["updated_at"]),
        )

    if previous_status != "APPROVED":
        raise HTTPException(
            status_code=422,
            detail={
                "type": "INVALID_SETTLEMENT_STATUS_TRANSITION",
                "message": "Pagamento exige batch em status APPROVED.",
                "current_status": previous_status,
            },
        )

    db.execute(
        text(
            """
            UPDATE partner_settlement_batches
            SET status = 'PAID',
                settled_at = NOW(),
                settlement_ref = COALESCE(:settlement_ref, settlement_ref),
                notes = COALESCE(:notes, notes),
                updated_at = NOW()
            WHERE id = :batch_id AND partner_id = :partner_id
            """
        ),
        {
            "batch_id": batch_id,
            "partner_id": partner_id,
            "settlement_ref": (payload.settlement_ref.strip() if payload.settlement_ref else None),
            "notes": (payload.notes.strip() if payload.notes else None),
        },
    )
    _audit_ops(
        db=db,
        action="PARTNER_SETTLEMENT_PAY",
        result="SUCCESS",
        correlation_id=corr_id,
        user_id=str(current_user.id),
        details={
            "partner_id": partner_id,
            "before": {"id": batch_id, "status": previous_status},
            "after": {"id": batch_id, "status": "PAID"},
        },
    )
    db.commit()
    row = db.execute(
        text(
            """
            SELECT
                id, partner_id, partner_type, period_start, period_end, currency,
                total_orders, gross_revenue_cents, revenue_share_pct, revenue_share_cents,
                fees_cents, net_amount_cents, status, settled_at, settlement_ref,
                notes, created_at, updated_at
            FROM partner_settlement_batches
            WHERE id = :batch_id
            """
        ),
        {"batch_id": batch_id},
    ).mappings().first()
    return PartnerSettlementOut(
        id=str(row["id"]),
        partner_id=str(row["partner_id"]),
        partner_type=str(row["partner_type"]),
        period_start=row["period_start"].isoformat(),
        period_end=row["period_end"].isoformat(),
        currency=str(row["currency"] or "BRL"),
        total_orders=int(row["total_orders"] or 0),
        gross_revenue_cents=int(row["gross_revenue_cents"] or 0),
        revenue_share_pct=float(row["revenue_share_pct"] or 0),
        revenue_share_cents=int(row["revenue_share_cents"] or 0),
        fees_cents=int(row["fees_cents"] or 0),
        net_amount_cents=int(row["net_amount_cents"] or 0),
        status=str(row["status"]),
        settled_at=_to_iso_utc(row["settled_at"]) if row["settled_at"] else None,
        settlement_ref=str(row["settlement_ref"]) if row["settlement_ref"] else None,
        notes=str(row["notes"]) if row["notes"] else None,
        created_at=_to_iso_utc(row["created_at"]),
        updated_at=_to_iso_utc(row["updated_at"]),
    )


@router.get("/{partner_id}/settlements/{batch_id}/items", response_model=PartnerSettlementItemListOut)
def get_partner_settlement_items(
    partner_id: str,
    batch_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    _load_partner_status(db, partner_id=partner_id)
    batch = db.execute(
        text("SELECT id FROM partner_settlement_batches WHERE id = :batch_id AND partner_id = :partner_id"),
        {"batch_id": batch_id, "partner_id": partner_id},
    ).mappings().first()
    if not batch:
        raise HTTPException(status_code=404, detail={"type": "SETTLEMENT_NOT_FOUND", "message": "Batch de liquidação não encontrado."})

    totals = db.execute(
        text(
            """
            SELECT
                COUNT(*)::int AS total,
                COALESCE(SUM(gross_cents), 0)::bigint AS gross_total_cents,
                COALESCE(SUM(share_cents), 0)::bigint AS share_total_cents
            FROM partner_settlement_items
            WHERE batch_id = :batch_id
            """
        ),
        {"batch_id": batch_id},
    ).mappings().first() or {}
    rows = db.execute(
        text(
            """
            SELECT id, batch_id, order_id, order_date, gross_cents, share_pct, share_cents, currency
            FROM partner_settlement_items
            WHERE batch_id = :batch_id
            ORDER BY order_date DESC, id DESC
            LIMIT :limit OFFSET :offset
            """
        ),
        {"batch_id": batch_id, "limit": int(limit), "offset": int(offset)},
    ).mappings().all()
    items = [
        PartnerSettlementItemOut(
            id=int(row["id"]),
            batch_id=str(row["batch_id"]),
            order_id=str(row["order_id"]),
            order_date=_to_iso_utc(row["order_date"]),
            gross_cents=int(row["gross_cents"] or 0),
            share_pct=float(row["share_pct"] or 0),
            share_cents=int(row["share_cents"] or 0),
            currency=str(row["currency"] or "BRL"),
        )
        for row in rows
    ]
    return PartnerSettlementItemListOut(
        ok=True,
        total=int(totals.get("total") or 0),
        limit=int(limit),
        offset=int(offset),
        gross_total_cents=int(totals.get("gross_total_cents") or 0),
        share_total_cents=int(totals.get("share_total_cents") or 0),
        items=items,
    )


@router.get("/{partner_id}/settlements/{batch_id}/reconciliation", response_model=PartnerSettlementReconciliationOut)
def get_partner_settlement_reconciliation(
    partner_id: str,
    batch_id: str,
    current_user: User = Depends(get_current_user),
    correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    db: Session = Depends(get_db),
):
    corr_id = _resolve_correlation_id(correlation_id)
    _load_partner_status(db, partner_id=partner_id)
    batch = db.execute(
        text(
            """
            SELECT
                id, partner_id, status, total_orders, gross_revenue_cents, revenue_share_cents
            FROM partner_settlement_batches
            WHERE id = :batch_id AND partner_id = :partner_id
            """
        ),
        {"batch_id": batch_id, "partner_id": partner_id},
    ).mappings().first()
    if not batch:
        raise HTTPException(status_code=404, detail={"type": "SETTLEMENT_NOT_FOUND", "message": "Batch de liquidação não encontrado."})

    items_totals = db.execute(
        text(
            """
            SELECT
                COUNT(*)::int AS total_orders,
                COALESCE(SUM(gross_cents), 0)::bigint AS gross_revenue_cents,
                COALESCE(SUM(share_cents), 0)::bigint AS revenue_share_cents
            FROM partner_settlement_items
            WHERE batch_id = :batch_id
            """
        ),
        {"batch_id": batch_id},
    ).mappings().first() or {}

    expected_total_orders = int(batch.get("total_orders") or 0)
    expected_gross_revenue_cents = int(batch.get("gross_revenue_cents") or 0)
    expected_revenue_share_cents = int(batch.get("revenue_share_cents") or 0)
    actual_total_orders = int(items_totals.get("total_orders") or 0)
    actual_gross_revenue_cents = int(items_totals.get("gross_revenue_cents") or 0)
    actual_revenue_share_cents = int(items_totals.get("revenue_share_cents") or 0)

    delta_total_orders = actual_total_orders - expected_total_orders
    delta_gross_revenue_cents = actual_gross_revenue_cents - expected_gross_revenue_cents
    delta_revenue_share_cents = actual_revenue_share_cents - expected_revenue_share_cents
    has_divergence = any(
        [
            delta_total_orders != 0,
            delta_gross_revenue_cents != 0,
            delta_revenue_share_cents != 0,
        ]
    )

    alerts: list[PartnerSettlementReconciliationAlertOut] = []
    if has_divergence:
        severity = _settlement_reconciliation_severity(
            delta_total_orders=delta_total_orders,
            delta_gross_revenue_cents=delta_gross_revenue_cents,
            delta_revenue_share_cents=delta_revenue_share_cents,
        )
        alerts.append(
            PartnerSettlementReconciliationAlertOut(
                code="SETTLEMENT_RECONCILIATION_DIVERGENCE",
                severity=severity,
                title="Divergência no fechamento financeiro",
                message=(
                    "Diferença entre totais do batch e somatório dos itens. "
                    "Escalar para comitê operacional para validação e correção."
                ),
            )
        )

    _audit_ops(
        db=db,
        action="PARTNER_SETTLEMENT_RECONCILIATION_CHECK",
        result=("WARNING" if has_divergence else "SUCCESS"),
        correlation_id=corr_id,
        user_id=str(current_user.id),
        details={
            "partner_id": partner_id,
            "batch_id": batch_id,
            "has_divergence": has_divergence,
            "delta_total_orders": delta_total_orders,
            "delta_gross_revenue_cents": delta_gross_revenue_cents,
            "delta_revenue_share_cents": delta_revenue_share_cents,
            "alerts": [alert.model_dump() for alert in alerts],
        },
    )
    db.commit()

    return PartnerSettlementReconciliationOut(
        ok=True,
        partner_id=partner_id,
        batch_id=batch_id,
        status=str(batch.get("status") or ""),
        has_divergence=has_divergence,
        expected_total_orders=expected_total_orders,
        expected_gross_revenue_cents=expected_gross_revenue_cents,
        expected_revenue_share_cents=expected_revenue_share_cents,
        actual_total_orders=actual_total_orders,
        actual_gross_revenue_cents=actual_gross_revenue_cents,
        actual_revenue_share_cents=actual_revenue_share_cents,
        delta_total_orders=delta_total_orders,
        delta_gross_revenue_cents=delta_gross_revenue_cents,
        delta_revenue_share_cents=delta_revenue_share_cents,
        alerts=alerts,
    )


@router.get("/ops/settlements/reconciliation-alerts", response_model=PartnerSettlementReconciliationAlertTimelineOut)
def get_ops_settlement_reconciliation_alerts(
    from_: str | None = Query(default=None, alias="from"),
    to: str | None = Query(default=None),
    partner_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    dt_to = _parse_iso_datetime_utc_optional(to, field_name="to") or datetime.now(timezone.utc)
    dt_from = _parse_iso_datetime_utc_optional(from_, field_name="from") or (dt_to - timedelta(days=30))
    if dt_from > dt_to:
        raise HTTPException(
            status_code=422,
            detail={"type": "INVALID_DATE_RANGE", "message": "from deve ser <= to."},
        )

    rows = db.query(OpsActionAudit).filter(
        OpsActionAudit.action == "PARTNER_SETTLEMENT_RECONCILIATION_CHECK",
        OpsActionAudit.created_at >= dt_from,
        OpsActionAudit.created_at <= dt_to,
    ).order_by(OpsActionAudit.created_at.desc(), OpsActionAudit.id.desc()).limit(5000).all()

    filtered: list[OpsActionAudit] = []
    for row in rows:
        details = _json_load_dict(row.details_json, default={})
        if not bool(details.get("has_divergence")):
            continue
        row_partner = str(details.get("partner_id") or "")
        if str(partner_id or "").strip() and row_partner != str(partner_id).strip():
            continue
        filtered.append(row)

    total = len(filtered)
    paged = filtered[int(offset): int(offset) + int(limit)]
    items: list[PartnerSettlementReconciliationAlertTimelineItemOut] = []
    for row in paged:
        details = _json_load_dict(row.details_json, default={})
        alert_items = details.get("alerts") if isinstance(details.get("alerts"), list) else []
        first_alert = alert_items[0] if alert_items else {}
        items.append(
            PartnerSettlementReconciliationAlertTimelineItemOut(
                audit_id=str(row.id),
                created_at=_to_iso_utc(row.created_at),
                partner_id=str(details.get("partner_id") or ""),
                batch_id=str(details.get("batch_id") or ""),
                severity=str(first_alert.get("severity") or "HIGH"),
                message=str(first_alert.get("message") or "Divergência de reconciliação detectada."),
                delta_total_orders=int(details.get("delta_total_orders") or 0),
                delta_gross_revenue_cents=int(details.get("delta_gross_revenue_cents") or 0),
                delta_revenue_share_cents=int(details.get("delta_revenue_share_cents") or 0),
            )
        )

    return PartnerSettlementReconciliationAlertTimelineOut(
        ok=True,
        **{"from": _to_iso_utc(dt_from), "to": _to_iso_utc(dt_to)},
        total=total,
        limit=int(limit),
        offset=int(offset),
        items=items,
    )


@router.post("/ops/settlements/reconciliation/run", response_model=PartnerSettlementReconciliationBatchRunOut)
def post_ops_settlement_reconciliation_run(
    from_: str | None = Query(default=None, alias="from"),
    to: str | None = Query(default=None),
    partner_id: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    dry_run: bool = Query(default=True),
    confirm_live_run: bool = Query(default=False),
    current_user: User = Depends(get_current_user),
    correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    db: Session = Depends(get_db),
):
    corr_id = _resolve_correlation_id(correlation_id)
    live_run_limit_guard = 200
    if not dry_run and not bool(confirm_live_run):
        raise HTTPException(
            status_code=422,
            detail={
                "type": "LIVE_RUN_CONFIRMATION_REQUIRED",
                "message": "Para dry_run=false, informe confirm_live_run=true.",
            },
        )
    if not dry_run and int(limit) > live_run_limit_guard:
        raise HTTPException(
            status_code=422,
            detail={
                "type": "LIVE_RUN_LIMIT_EXCEEDED",
                "message": "Para execucao real, limit deve ser <= 200.",
                "max_limit": live_run_limit_guard,
            },
        )

    dt_to = _parse_iso_datetime_utc_optional(to, field_name="to") or datetime.now(timezone.utc)
    dt_from = _parse_iso_datetime_utc_optional(from_, field_name="from") or (dt_to - timedelta(days=30))
    if dt_from > dt_to:
        raise HTTPException(
            status_code=422,
            detail={"type": "INVALID_DATE_RANGE", "message": "from deve ser <= to."},
        )

    where_parts = [
        "created_at >= :dt_from",
        "created_at <= :dt_to",
        "status IN ('DRAFT','APPROVED','PAID')",
    ]
    params: dict[str, object] = {"dt_from": dt_from, "dt_to": dt_to, "limit": int(limit)}
    normalized_partner = str(partner_id or "").strip()
    if normalized_partner:
        where_parts.append("partner_id = :partner_id")
        params["partner_id"] = normalized_partner
    where_sql = " AND ".join(where_parts)

    batches = db.execute(
        text(
            f"""
            SELECT id, partner_id, status, total_orders, gross_revenue_cents, revenue_share_cents
            FROM partner_settlement_batches
            WHERE {where_sql}
            ORDER BY created_at DESC, id DESC
            LIMIT :limit
            """
        ),
        params,
    ).mappings().all()

    items: list[PartnerSettlementReconciliationBatchRunItemOut] = []
    divergent_batches = 0
    for batch in batches:
        batch_id = str(batch.get("id") or "")
        totals = db.execute(
            text(
                """
                SELECT
                    COUNT(*)::int AS total_orders,
                    COALESCE(SUM(gross_cents), 0)::bigint AS gross_revenue_cents,
                    COALESCE(SUM(share_cents), 0)::bigint AS revenue_share_cents
                FROM partner_settlement_items
                WHERE batch_id = :batch_id
                """
            ),
            {"batch_id": batch_id},
        ).mappings().first() or {}

        delta_total_orders = int(totals.get("total_orders") or 0) - int(batch.get("total_orders") or 0)
        delta_gross_revenue_cents = int(totals.get("gross_revenue_cents") or 0) - int(batch.get("gross_revenue_cents") or 0)
        delta_revenue_share_cents = int(totals.get("revenue_share_cents") or 0) - int(batch.get("revenue_share_cents") or 0)
        has_divergence = any(
            [
                delta_total_orders != 0,
                delta_gross_revenue_cents != 0,
                delta_revenue_share_cents != 0,
            ]
        )
        severity: str | None = None
        if has_divergence:
            divergent_batches += 1
            severity = _settlement_reconciliation_severity(
                delta_total_orders=delta_total_orders,
                delta_gross_revenue_cents=delta_gross_revenue_cents,
                delta_revenue_share_cents=delta_revenue_share_cents,
            )

        items.append(
            PartnerSettlementReconciliationBatchRunItemOut(
                batch_id=batch_id,
                partner_id=str(batch.get("partner_id") or ""),
                status=str(batch.get("status") or ""),
                has_divergence=has_divergence,
                delta_total_orders=delta_total_orders,
                delta_gross_revenue_cents=delta_gross_revenue_cents,
                delta_revenue_share_cents=delta_revenue_share_cents,
                severity=severity,
            )
        )

    scanned_batches = len(items)
    divergence_rate_pct = round((divergent_batches / scanned_batches) * 100.0, 2) if scanned_batches > 0 else 0.0
    if not dry_run:
        _audit_ops(
            db=db,
            action="PARTNER_SETTLEMENT_RECONCILIATION_BATCH_RUN",
            result=("WARNING" if divergent_batches > 0 else "SUCCESS"),
            correlation_id=corr_id,
            user_id=str(current_user.id),
            details={
                "from": _to_iso_utc(dt_from),
                "to": _to_iso_utc(dt_to),
                "partner_id": normalized_partner or None,
                "limit": int(limit),
                "dry_run": False,
                "confirm_live_run": True,
                "scanned_batches": scanned_batches,
                "divergent_batches": divergent_batches,
                "divergence_rate_pct": divergence_rate_pct,
                "items": [item.model_dump() for item in items[:200]],
            },
        )
        db.commit()

    return PartnerSettlementReconciliationBatchRunOut(
        ok=True,
        **{"from": _to_iso_utc(dt_from), "to": _to_iso_utc(dt_to)},
        partner_id=(normalized_partner or None),
        limit=int(limit),
        dry_run=bool(dry_run),
        confirm_live_run=bool(confirm_live_run),
        scanned_batches=scanned_batches,
        divergent_batches=divergent_batches,
        divergence_rate_pct=divergence_rate_pct,
        items=items,
    )


@router.get("/ops/settlements/reconciliation/compare", response_model=PartnerSettlementReconciliationCompareOut)
def get_ops_settlement_reconciliation_compare(
    from_: str | None = Query(default=None, alias="from"),
    to: str | None = Query(default=None),
    partner_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    current_to = _parse_iso_datetime_utc_optional(to, field_name="to") or datetime.now(timezone.utc)
    current_from = _parse_iso_datetime_utc_optional(from_, field_name="from") or (current_to - timedelta(days=30))
    if current_from > current_to:
        raise HTTPException(
            status_code=422,
            detail={"type": "INVALID_DATE_RANGE", "message": "from deve ser <= to."},
        )

    window_span = current_to - current_from
    previous_to = current_from
    previous_from = previous_to - window_span
    normalized_partner = str(partner_id or "").strip()

    def _calc_window_metrics(window_from: datetime, window_to: datetime) -> PartnerSettlementReconciliationCompareWindowOut:
        where_parts = [
            "created_at >= :dt_from",
            "created_at <= :dt_to",
            "status IN ('DRAFT','APPROVED','PAID')",
        ]
        params: dict[str, object] = {"dt_from": window_from, "dt_to": window_to}
        if normalized_partner:
            where_parts.append("partner_id = :partner_id")
            params["partner_id"] = normalized_partner
        where_sql = " AND ".join(where_parts)
        batches = db.execute(
            text(
                f"""
                SELECT id, total_orders, gross_revenue_cents, revenue_share_cents
                FROM partner_settlement_batches
                WHERE {where_sql}
                ORDER BY created_at DESC, id DESC
                LIMIT 5000
                """
            ),
            params,
        ).mappings().all()

        divergent_batches = 0
        for batch in batches:
            totals = db.execute(
                text(
                    """
                    SELECT
                        COUNT(*)::int AS total_orders,
                        COALESCE(SUM(gross_cents), 0)::bigint AS gross_revenue_cents,
                        COALESCE(SUM(share_cents), 0)::bigint AS revenue_share_cents
                    FROM partner_settlement_items
                    WHERE batch_id = :batch_id
                    """
                ),
                {"batch_id": str(batch.get("id") or "")},
            ).mappings().first() or {}
            if (
                int(totals.get("total_orders") or 0) != int(batch.get("total_orders") or 0)
                or int(totals.get("gross_revenue_cents") or 0) != int(batch.get("gross_revenue_cents") or 0)
                or int(totals.get("revenue_share_cents") or 0) != int(batch.get("revenue_share_cents") or 0)
            ):
                divergent_batches += 1

        scanned_batches = len(batches)
        divergence_rate_pct = round((divergent_batches / scanned_batches) * 100.0, 2) if scanned_batches > 0 else 0.0
        return PartnerSettlementReconciliationCompareWindowOut(
            scanned_batches=scanned_batches,
            divergent_batches=divergent_batches,
            divergence_rate_pct=divergence_rate_pct,
        )

    current = _calc_window_metrics(current_from, current_to)
    previous = _calc_window_metrics(previous_from, previous_to)

    return PartnerSettlementReconciliationCompareOut(
        ok=True,
        **{"from": _to_iso_utc(current_from), "to": _to_iso_utc(current_to)},
        previous_from=_to_iso_utc(previous_from),
        previous_to=_to_iso_utc(previous_to),
        partner_id=(normalized_partner or None),
        current=current,
        previous=previous,
        delta_scanned_batches_pct=_safe_delta_pct(current.scanned_batches, previous.scanned_batches),
        delta_divergent_batches_pct=_safe_delta_pct(current.divergent_batches, previous.divergent_batches),
        delta_divergence_rate_pct=round(current.divergence_rate_pct - previous.divergence_rate_pct, 2),
    )


@router.get("/ops/settlements/reconciliation/top-divergences", response_model=PartnerSettlementReconciliationTopDivergencesOut)
def get_ops_settlement_reconciliation_top_divergences(
    from_: str | None = Query(default=None, alias="from"),
    to: str | None = Query(default=None),
    partner_id: str | None = Query(default=None),
    top_n: int = Query(default=10, ge=1, le=200),
    min_severity: str | None = Query(
        default=None,
        description="Inclui divergencias com severidade >= ao nivel (HIGH > MEDIUM > LOW). Omitir retorna todas.",
    ),
    db: Session = Depends(get_db),
):
    min_sev = _parse_min_settlement_severity(min_severity)
    dt_to = _parse_iso_datetime_utc_optional(to, field_name="to") or datetime.now(timezone.utc)
    dt_from = _parse_iso_datetime_utc_optional(from_, field_name="from") or (dt_to - timedelta(days=30))
    if dt_from > dt_to:
        raise HTTPException(
            status_code=422,
            detail={"type": "INVALID_DATE_RANGE", "message": "from deve ser <= to."},
        )

    where_parts = [
        "created_at >= :dt_from",
        "created_at <= :dt_to",
        "status IN ('DRAFT','APPROVED','PAID')",
    ]
    params: dict[str, object] = {"dt_from": dt_from, "dt_to": dt_to}
    normalized_partner = str(partner_id or "").strip()
    if normalized_partner:
        where_parts.append("partner_id = :partner_id")
        params["partner_id"] = normalized_partner
    where_sql = " AND ".join(where_parts)

    batches = db.execute(
        text(
            f"""
            SELECT id, partner_id, status, total_orders, gross_revenue_cents, revenue_share_cents
            FROM partner_settlement_batches
            WHERE {where_sql}
            ORDER BY created_at DESC, id DESC
            LIMIT 5000
            """
        ),
        params,
    ).mappings().all()

    divergences: list[PartnerSettlementReconciliationTopDivergenceItemOut] = []
    severity_totals = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for batch in batches:
        batch_id = str(batch.get("id") or "")
        totals = db.execute(
            text(
                """
                SELECT
                    COUNT(*)::int AS total_orders,
                    COALESCE(SUM(gross_cents), 0)::bigint AS gross_revenue_cents,
                    COALESCE(SUM(share_cents), 0)::bigint AS revenue_share_cents
                FROM partner_settlement_items
                WHERE batch_id = :batch_id
                """
            ),
            {"batch_id": batch_id},
        ).mappings().first() or {}

        delta_total_orders = int(totals.get("total_orders") or 0) - int(batch.get("total_orders") or 0)
        delta_gross_revenue_cents = int(totals.get("gross_revenue_cents") or 0) - int(batch.get("gross_revenue_cents") or 0)
        delta_revenue_share_cents = int(totals.get("revenue_share_cents") or 0) - int(batch.get("revenue_share_cents") or 0)
        if delta_total_orders == 0 and delta_gross_revenue_cents == 0 and delta_revenue_share_cents == 0:
            continue

        impact_score = (
            abs(delta_gross_revenue_cents)
            + abs(delta_revenue_share_cents)
            + (abs(delta_total_orders) * 100)
        )
        severity = _settlement_reconciliation_severity(
            delta_total_orders=delta_total_orders,
            delta_gross_revenue_cents=delta_gross_revenue_cents,
            delta_revenue_share_cents=delta_revenue_share_cents,
        )
        bucket = str(severity).strip().upper()
        if bucket in severity_totals:
            severity_totals[bucket] += 1
        else:
            severity_totals["MEDIUM"] += 1
        if not _settlement_severity_meets_minimum(severity=severity, min_severity=min_sev):
            continue
        divergences.append(
            PartnerSettlementReconciliationTopDivergenceItemOut(
                batch_id=batch_id,
                partner_id=str(batch.get("partner_id") or ""),
                status=str(batch.get("status") or ""),
                impact_score=int(impact_score),
                delta_total_orders=delta_total_orders,
                delta_gross_revenue_cents=delta_gross_revenue_cents,
                delta_revenue_share_cents=delta_revenue_share_cents,
                severity=severity,
            )
        )

    divergences.sort(key=lambda item: item.impact_score, reverse=True)
    top_items = divergences[: int(top_n)]
    return PartnerSettlementReconciliationTopDivergencesOut(
        ok=True,
        **{"from": _to_iso_utc(dt_from), "to": _to_iso_utc(dt_to)},
        partner_id=(normalized_partner or None),
        top_n=int(top_n),
        min_severity=min_sev,
        severity_counts=PartnerSettlementReconciliationTopDivergenceSeverityCountsOut.model_validate(severity_totals),
        total_divergent_batches=len(divergences),
        items=top_items,
    )


@router.get("/{partner_id}/performance", response_model=PartnerPerformanceListOut)
def get_partner_performance(
    partner_id: str,
    limit: int = Query(default=6, ge=1, le=24),
    db: Session = Depends(get_db),
):
    _load_partner_status(db, partner_id=partner_id)
    rows = db.execute(
        text(
            """
            SELECT
                id, partner_id, period_month, total_orders,
                on_time_pickup_pct, return_rate_pct, avg_pickup_hours,
                sla_compliance_pct, webhook_success_rate, generated_at
            FROM partner_performance_metrics
            WHERE partner_id = :partner_id
            ORDER BY period_month DESC, generated_at DESC
            LIMIT :limit
            """
        ),
        {"partner_id": partner_id, "limit": int(limit)},
    ).mappings().all()
    items = [
        PartnerPerformanceOut(
            id=str(row["id"]),
            partner_id=str(row["partner_id"]),
            period_month=str(row["period_month"]),
            total_orders=int(row["total_orders"] or 0),
            on_time_pickup_pct=(float(row["on_time_pickup_pct"]) if row["on_time_pickup_pct"] is not None else None),
            return_rate_pct=(float(row["return_rate_pct"]) if row["return_rate_pct"] is not None else None),
            avg_pickup_hours=(float(row["avg_pickup_hours"]) if row["avg_pickup_hours"] is not None else None),
            sla_compliance_pct=(float(row["sla_compliance_pct"]) if row["sla_compliance_pct"] is not None else None),
            webhook_success_rate=(float(row["webhook_success_rate"]) if row["webhook_success_rate"] is not None else None),
            generated_at=_to_iso_utc(row["generated_at"]),
        )
        for row in rows
    ]
    return PartnerPerformanceListOut(ok=True, total=len(items), items=items)


@router.get("/{partner_id}/service-areas", response_model=PartnerServiceAreaListOut)
def get_partner_service_areas(
    partner_id: str,
    only_active: bool = Query(default=True),
    limit: int = Query(default=200, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    _load_partner_status(db, partner_id=partner_id)
    rows = db.execute(
        text(
            """
            SELECT id, partner_id, partner_type, locker_id, priority, exclusive,
                   valid_from, valid_until, is_active, created_at
            FROM partner_service_areas
            WHERE partner_id = :partner_id
              AND (:only_active IS FALSE OR is_active IS TRUE)
            ORDER BY priority ASC, created_at DESC
            LIMIT :limit
            """
        ),
        {"partner_id": partner_id, "only_active": bool(only_active), "limit": int(limit)},
    ).mappings().all()
    items = [
        PartnerServiceAreaOut(
            id=str(row["id"]),
            partner_id=str(row["partner_id"]),
            partner_type=str(row["partner_type"]),
            locker_id=str(row["locker_id"]),
            priority=int(row["priority"] or 0),
            exclusive=bool(row["exclusive"]),
            valid_from=row["valid_from"].isoformat(),
            valid_until=(row["valid_until"].isoformat() if row["valid_until"] else None),
            is_active=bool(row["is_active"]),
            created_at=_to_iso_utc(row["created_at"]),
        )
        for row in rows
    ]
    return PartnerServiceAreaListOut(ok=True, total=len(items), items=items)


@router.post("/{partner_id}/service-areas", response_model=PartnerServiceAreaOut)
def post_partner_service_area(
    partner_id: str,
    payload: PartnerServiceAreaIn,
    current_user: User = Depends(get_current_user),
    correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
    db: Session = Depends(get_db),
):
    corr_id = _resolve_correlation_id(correlation_id)
    _load_partner_status(db, partner_id=partner_id)
    valid_from = _parse_iso_date(payload.valid_from, field_name="valid_from")
    valid_until = _parse_iso_date(payload.valid_until, field_name="valid_until") if payload.valid_until else None
    if valid_until and valid_until < valid_from:
        raise HTTPException(status_code=422, detail={"type": "INVALID_DATE_RANGE", "message": "valid_until deve ser >= valid_from."})

    area_id = str(uuid4())
    db.execute(
        text(
            """
            INSERT INTO partner_service_areas (
                id, partner_id, partner_type, locker_id, priority, exclusive,
                valid_from, valid_until, is_active, created_at
            ) VALUES (
                :id, :partner_id, 'ECOMMERCE', :locker_id, :priority, :exclusive,
                :valid_from, :valid_until, :is_active, NOW()
            )
            """
        ),
        {
            "id": area_id,
            "partner_id": partner_id,
            "locker_id": payload.locker_id.strip(),
            "priority": int(payload.priority),
            "exclusive": bool(payload.exclusive),
            "valid_from": valid_from,
            "valid_until": valid_until,
            "is_active": bool(payload.is_active),
        },
    )
    _audit_ops(
        db=db,
        action="PARTNER_SERVICE_AREA_CREATE",
        result="SUCCESS",
        correlation_id=corr_id,
        user_id=str(current_user.id),
        details={
            "partner_id": partner_id,
            "after": {
                "id": area_id,
                "locker_id": payload.locker_id.strip(),
                "priority": int(payload.priority),
                "exclusive": bool(payload.exclusive),
                "valid_from": valid_from.isoformat(),
                "valid_until": (valid_until.isoformat() if valid_until else None),
                "is_active": bool(payload.is_active),
            },
        },
    )
    db.commit()
    row = db.execute(
        text(
            """
            SELECT id, partner_id, partner_type, locker_id, priority, exclusive,
                   valid_from, valid_until, is_active, created_at
            FROM partner_service_areas
            WHERE id = :id
            """
        ),
        {"id": area_id},
    ).mappings().first()
    return PartnerServiceAreaOut(
        id=str(row["id"]),
        partner_id=str(row["partner_id"]),
        partner_type=str(row["partner_type"]),
        locker_id=str(row["locker_id"]),
        priority=int(row["priority"] or 0),
        exclusive=bool(row["exclusive"]),
        valid_from=row["valid_from"].isoformat(),
        valid_until=(row["valid_until"].isoformat() if row["valid_until"] else None),
        is_active=bool(row["is_active"]),
        created_at=_to_iso_utc(row["created_at"]),
    )


@router.post("/{partner_id}/products", response_model=PartnerProductCreateOut)
def post_partner_product(
    partner_id: str,
    payload: PartnerProductCreateIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_partner_is_active_for_catalog(db, partner_id=partner_id)

    product_id = str(payload.id or "").strip()
    if not product_id:
        raise HTTPException(
            status_code=422,
            detail={"type": "INVALID_PRODUCT_ID", "message": "id do produto é obrigatório."},
        )

    existing_product = db.execute(
        text("SELECT id FROM products WHERE id = :id"),
        {"id": product_id},
    ).fetchone()
    if existing_product:
        raise HTTPException(
            status_code=409,
            detail={
                "type": "PRODUCT_ALREADY_EXISTS",
                "message": "Produto já cadastrado para este id.",
                "product_id": product_id,
            },
        )

    category_exists = db.execute(
        text("SELECT id FROM product_categories WHERE id = :category_id"),
        {"category_id": payload.category_id},
    ).fetchone()
    if not category_exists:
        raise HTTPException(
            status_code=422,
            detail={
                "type": "INVALID_CATEGORY",
                "message": "Categoria não encontrada em product_categories.",
                "category_id": payload.category_id,
            },
        )

    eligible_lockers_count_row = db.execute(
        text(
            """
            SELECT COUNT(DISTINCT psa.locker_id) AS total
            FROM partner_service_areas psa
            JOIN locker_slot_configs lsc
              ON lsc.locker_id = psa.locker_id
            JOIN product_locker_configs plc
              ON plc.locker_id = psa.locker_id
             AND plc.category = :category_id
             AND plc.allowed = TRUE
            WHERE psa.partner_id = :partner_id
              AND psa.is_active = TRUE
              AND psa.valid_from <= CURRENT_DATE
              AND (psa.valid_until IS NULL OR psa.valid_until >= CURRENT_DATE)
              AND lsc.width_mm >= :width_mm
              AND lsc.height_mm >= :height_mm
              AND lsc.depth_mm >= :depth_mm
              AND lsc.max_weight_g >= :weight_g
            """
        ),
        {
            "partner_id": partner_id,
            "category_id": payload.category_id,
            "width_mm": payload.width_mm,
            "height_mm": payload.height_mm,
            "depth_mm": payload.depth_mm,
            "weight_g": payload.weight_g,
        },
    ).mappings().first()
    eligible_lockers_count = int((eligible_lockers_count_row or {}).get("total") or 0)

    recommended_row = db.execute(
        text(
            """
            SELECT
                psa.locker_id AS locker_id,
                lsc.slot_size AS slot_size
            FROM partner_service_areas psa
            JOIN locker_slot_configs lsc
              ON lsc.locker_id = psa.locker_id
            JOIN product_locker_configs plc
              ON plc.locker_id = psa.locker_id
             AND plc.category = :category_id
             AND plc.allowed = TRUE
            WHERE psa.partner_id = :partner_id
              AND psa.is_active = TRUE
              AND psa.valid_from <= CURRENT_DATE
              AND (psa.valid_until IS NULL OR psa.valid_until >= CURRENT_DATE)
              AND lsc.width_mm >= :width_mm
              AND lsc.height_mm >= :height_mm
              AND lsc.depth_mm >= :depth_mm
              AND lsc.max_weight_g >= :weight_g
            ORDER BY
              psa.priority DESC,
              CASE lsc.slot_size
                WHEN 'XS' THEN 1
                WHEN 'S' THEN 2
                WHEN 'P' THEN 2
                WHEN 'M' THEN 3
                WHEN 'G' THEN 4
                WHEN 'L' THEN 4
                WHEN 'XG' THEN 5
                ELSE 99
              END ASC,
              psa.locker_id ASC
            LIMIT 1
            """
        ),
        {
            "partner_id": partner_id,
            "category_id": payload.category_id,
            "width_mm": payload.width_mm,
            "height_mm": payload.height_mm,
            "depth_mm": payload.depth_mm,
            "weight_g": payload.weight_g,
        },
    ).mappings().first()

    if not recommended_row:
        raise HTTPException(
            status_code=422,
            detail={
                "type": "PRODUCT_NOT_ELIGIBLE",
                "message": "Produto não cabe em nenhum locker ativo do parceiro para a categoria informada.",
                "partner_id": partner_id,
                "category_id": payload.category_id,
            },
        )

    now = datetime.now(timezone.utc)
    db.execute(
        text(
            """
            INSERT INTO products (
                id,
                name,
                description,
                amount_cents,
                currency,
                category_id,
                width_mm,
                height_mm,
                depth_mm,
                weight_g,
                is_active,
                requires_age_verification,
                requires_id_check,
                requires_signature,
                is_hazardous,
                is_fragile,
                metadata_json,
                created_at,
                updated_at,
                status
            ) VALUES (
                :id,
                :name,
                :description,
                :amount_cents,
                :currency,
                :category_id,
                :width_mm,
                :height_mm,
                :depth_mm,
                :weight_g,
                FALSE,
                :requires_age_verification,
                :requires_id_check,
                :requires_signature,
                :is_hazardous,
                :is_fragile,
                CAST(:metadata_json AS JSONB),
                :created_at,
                :updated_at,
                'DRAFT'
            )
            """
        ),
        {
            "id": product_id,
            "name": payload.name.strip(),
            "description": (payload.description.strip() if payload.description else None),
            "amount_cents": int(payload.amount_cents),
            "currency": str(payload.currency or "BRL").strip().upper(),
            "category_id": payload.category_id.strip(),
            "width_mm": int(payload.width_mm),
            "height_mm": int(payload.height_mm),
            "depth_mm": int(payload.depth_mm),
            "weight_g": int(payload.weight_g),
            "requires_age_verification": bool(payload.requires_age_verification),
            "requires_id_check": bool(payload.requires_id_check),
            "requires_signature": bool(payload.requires_signature),
            "is_hazardous": bool(payload.is_hazardous),
            "is_fragile": bool(payload.is_fragile),
            "metadata_json": json.dumps(payload.metadata_json or {}),
            "created_at": now,
            "updated_at": now,
        },
    )

    db.execute(
        text(
            """
            INSERT INTO product_status_history (
                id,
                product_id,
                from_status,
                to_status,
                reason,
                changed_by,
                changed_at
            ) VALUES (
                :id,
                :product_id,
                NULL,
                'DRAFT',
                :reason,
                :changed_by,
                :changed_at
            )
            """
        ),
        {
            "id": str(uuid4()),
            "product_id": product_id,
            "reason": "Partner product registration with eligibility validation",
            "changed_by": (str(current_user.id) if current_user and current_user.id else None),
            "changed_at": now,
        },
    )
    db.commit()

    return PartnerProductCreateOut(
        ok=True,
        product_id=product_id,
        partner_id=partner_id,
        status="DRAFT",
        eligibility_ok=True,
        recommended_locker_id=str(recommended_row["locker_id"]),
        recommended_slot_size=str(recommended_row["slot_size"]),
        eligible_lockers_count=eligible_lockers_count,
        reason=None,
    )


@router.get("/{partner_id}/lockers/{locker_id}/eligible-products", response_model=PartnerEligibleProductListOut)
def get_partner_locker_eligible_products(
    partner_id: str,
    locker_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    _ensure_partner_is_active_for_catalog(db, partner_id=partner_id)

    psa_exists = db.execute(
        text(
            """
            SELECT 1
            FROM partner_service_areas psa
            WHERE psa.partner_id = :partner_id
              AND psa.locker_id = :locker_id
              AND psa.is_active = TRUE
              AND psa.valid_from <= CURRENT_DATE
              AND (psa.valid_until IS NULL OR psa.valid_until >= CURRENT_DATE)
            LIMIT 1
            """
        ),
        {"partner_id": partner_id, "locker_id": locker_id},
    ).fetchone()
    if not psa_exists:
        raise HTTPException(
            status_code=422,
            detail={
                "type": "LOCKER_NOT_IN_PARTNER_SERVICE_AREA",
                "message": "Locker não está ativo na área de atendimento do parceiro.",
                "partner_id": partner_id,
                "locker_id": locker_id,
            },
        )

    total_row = db.execute(
        text(
            """
            SELECT COUNT(*) AS total
            FROM products p
            WHERE COALESCE(p.status, 'DRAFT') = 'ACTIVE'
              AND EXISTS (
                    SELECT 1
                    FROM product_locker_configs plc
                    WHERE plc.locker_id = :locker_id
                      AND plc.category = p.category_id
                      AND plc.allowed = TRUE
              )
              AND EXISTS (
                    SELECT 1
                    FROM locker_slot_configs lsc
                    WHERE lsc.locker_id = :locker_id
                      AND lsc.width_mm >= p.width_mm
                      AND lsc.height_mm >= p.height_mm
                      AND lsc.depth_mm >= p.depth_mm
                      AND lsc.max_weight_g >= p.weight_g
              )
            """
        ),
        {"locker_id": locker_id},
    ).mappings().first()
    total = int((total_row or {}).get("total") or 0)

    rows = db.execute(
        text(
            """
            WITH ranked_slots AS (
                SELECT
                    p.id AS product_id,
                    p.name,
                    p.category_id,
                    COALESCE(p.status, 'DRAFT') AS status,
                    p.width_mm,
                    p.height_mm,
                    p.depth_mm,
                    p.weight_g,
                    lsc.slot_size,
                    ROW_NUMBER() OVER (
                        PARTITION BY p.id
                        ORDER BY
                            CASE lsc.slot_size
                                WHEN 'XS' THEN 1
                                WHEN 'S' THEN 2
                                WHEN 'P' THEN 2
                                WHEN 'M' THEN 3
                                WHEN 'G' THEN 4
                                WHEN 'L' THEN 4
                                WHEN 'XG' THEN 5
                                ELSE 99
                            END ASC
                    ) AS rn
                FROM products p
                JOIN product_locker_configs plc
                  ON plc.locker_id = :locker_id
                 AND plc.category = p.category_id
                 AND plc.allowed = TRUE
                JOIN locker_slot_configs lsc
                  ON lsc.locker_id = :locker_id
                 AND lsc.width_mm >= p.width_mm
                 AND lsc.height_mm >= p.height_mm
                 AND lsc.depth_mm >= p.depth_mm
                 AND lsc.max_weight_g >= p.weight_g
                WHERE COALESCE(p.status, 'DRAFT') = 'ACTIVE'
            )
            SELECT
                product_id,
                name,
                category_id,
                status,
                slot_size AS recommended_slot_size,
                width_mm,
                height_mm,
                depth_mm,
                weight_g
            FROM ranked_slots
            WHERE rn = 1
            ORDER BY name ASC, product_id ASC
            LIMIT :limit OFFSET :offset
            """
        ),
        {"locker_id": locker_id, "limit": int(limit), "offset": int(offset)},
    ).mappings().all()

    items = [
        PartnerEligibleProductItemOut(
            product_id=str(row["product_id"]),
            name=str(row["name"] or ""),
            category_id=(str(row["category_id"]) if row["category_id"] is not None else None),
            status=str(row["status"] or "DRAFT"),
            recommended_slot_size=str(row["recommended_slot_size"] or ""),
            width_mm=int(row["width_mm"] or 0),
            height_mm=int(row["height_mm"] or 0),
            depth_mm=int(row["depth_mm"] or 0),
            weight_g=int(row["weight_g"] or 0),
        )
        for row in rows
    ]

    return PartnerEligibleProductListOut(
        ok=True,
        partner_id=partner_id,
        locker_id=locker_id,
        total=total,
        limit=int(limit),
        offset=int(offset),
        items=items,
    )


@router.post("/{partner_id}/lockers/{locker_id}/slot-allocations/pick", response_model=PartnerSlotAllocationPickOut)
def post_partner_locker_slot_allocation_pick(
    partner_id: str,
    locker_id: str,
    payload: PartnerSlotAllocationPickIn,
    db: Session = Depends(get_db),
):
    _ensure_partner_is_active_for_catalog(db, partner_id=partner_id)

    psa_exists = db.execute(
        text(
            """
            SELECT 1
            FROM partner_service_areas psa
            WHERE psa.partner_id = :partner_id
              AND psa.locker_id = :locker_id
              AND psa.is_active = TRUE
              AND psa.valid_from <= CURRENT_DATE
              AND (psa.valid_until IS NULL OR psa.valid_until >= CURRENT_DATE)
            LIMIT 1
            """
        ),
        {"partner_id": partner_id, "locker_id": locker_id},
    ).fetchone()
    if not psa_exists:
        raise HTTPException(
            status_code=422,
            detail={
                "type": "LOCKER_NOT_IN_PARTNER_SERVICE_AREA",
                "message": "Locker não está ativo na área de atendimento do parceiro.",
                "partner_id": partner_id,
                "locker_id": locker_id,
            },
        )

    product_row = db.execute(
        text(
            """
            SELECT
                p.id,
                p.category_id,
                p.width_mm,
                p.height_mm,
                p.depth_mm,
                p.weight_g,
                COALESCE(p.status, 'DRAFT') AS status
            FROM products p
            WHERE p.id = :product_id
            """
        ),
        {"product_id": payload.product_id},
    ).mappings().first()
    if not product_row:
        raise HTTPException(
            status_code=404,
            detail={
                "type": "PRODUCT_NOT_FOUND",
                "message": "Produto não encontrado.",
                "product_id": payload.product_id,
            },
        )
    if str(product_row["status"]).upper() != "ACTIVE":
        raise HTTPException(
            status_code=422,
            detail={
                "type": "PRODUCT_NOT_ACTIVE",
                "message": "Produto precisa estar ACTIVE para alocação de slot.",
                "product_id": payload.product_id,
                "status": str(product_row["status"]),
            },
        )

    allocation_id = str(payload.allocation_id or f"al_{uuid4().hex[:24]}")
    slot_row = db.execute(
        text(
            """
            WITH best_slot AS (
                SELECT
                    ls.id,
                    ls.slot_label,
                    ls.slot_size
                FROM locker_slots ls
                JOIN locker_slot_configs lsc
                  ON lsc.locker_id = ls.locker_id
                 AND lsc.slot_size = ls.slot_size
                JOIN product_locker_configs plc
                  ON plc.locker_id = ls.locker_id
                 AND plc.category = :category_id
                 AND plc.allowed = TRUE
                WHERE ls.locker_id = :locker_id
                  AND ls.status = 'AVAILABLE'
                  AND lsc.width_mm >= :width_mm
                  AND lsc.height_mm >= :height_mm
                  AND lsc.depth_mm >= :depth_mm
                  AND lsc.max_weight_g >= :weight_g
                ORDER BY
                    CASE ls.slot_size
                        WHEN 'XS' THEN 1
                        WHEN 'S' THEN 2
                        WHEN 'P' THEN 2
                        WHEN 'M' THEN 3
                        WHEN 'G' THEN 4
                        WHEN 'L' THEN 4
                        WHEN 'XG' THEN 5
                        ELSE 99
                    END ASC,
                    ls.last_opened_at ASC NULLS FIRST,
                    ls.slot_label ASC
                LIMIT 1
                FOR UPDATE SKIP LOCKED
            )
            UPDATE locker_slots ls
            SET
                status = 'OCCUPIED',
                occupied_since = NOW(),
                current_allocation_id = :allocation_id,
                updated_at = NOW()
            FROM best_slot
            WHERE ls.id = best_slot.id
            RETURNING ls.id, ls.slot_label, ls.slot_size
            """
        ),
        {
            "locker_id": locker_id,
            "category_id": str(product_row["category_id"] or ""),
            "width_mm": int(product_row["width_mm"] or 0),
            "height_mm": int(product_row["height_mm"] or 0),
            "depth_mm": int(product_row["depth_mm"] or 0),
            "weight_g": int(product_row["weight_g"] or 0),
            "allocation_id": allocation_id,
        },
    ).mappings().first()

    if not slot_row:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail={
                "type": "SLOT_NOT_AVAILABLE",
                "message": "Nenhum slot disponível para o produto no locker informado.",
                "partner_id": partner_id,
                "locker_id": locker_id,
                "product_id": payload.product_id,
            },
        )

    db.commit()

    slot_label = str(slot_row["slot_label"] or "")
    slot_number = 0
    if "-" in slot_label:
        raw_num = slot_label.split("-", 1)[1]
        if raw_num.isdigit():
            slot_number = int(raw_num)

    return PartnerSlotAllocationPickOut(
        ok=True,
        partner_id=partner_id,
        locker_id=locker_id,
        product_id=str(product_row["id"]),
        allocation_id=allocation_id,
        slot_id=str(slot_row["id"]),
        slot_label=slot_label,
        slot_size=str(slot_row["slot_size"] or ""),
        slot_number=slot_number,
        state="RESERVED_PENDING_PAYMENT",
    )


@router.post(
    "/{partner_id}/lockers/{locker_id}/slot-allocations/{allocation_id}/pickup-confirm",
    response_model=PartnerSlotAllocationPickupConfirmOut,
)
def post_partner_locker_slot_allocation_pickup_confirm(
    partner_id: str,
    locker_id: str,
    allocation_id: str,
    payload: PartnerSlotAllocationPickupConfirmIn,
    db: Session = Depends(get_db),
):
    _ensure_partner_is_active_for_catalog(db, partner_id=partner_id)
    _ = payload.note
    corr_id = _resolve_correlation_id(None)

    psa_exists = db.execute(
        text(
            """
            SELECT 1
            FROM partner_service_areas psa
            WHERE psa.partner_id = :partner_id
              AND psa.locker_id = :locker_id
              AND psa.is_active = TRUE
              AND psa.valid_from <= CURRENT_DATE
              AND (psa.valid_until IS NULL OR psa.valid_until >= CURRENT_DATE)
            LIMIT 1
            """
        ),
        {"partner_id": partner_id, "locker_id": locker_id},
    ).fetchone()
    if not psa_exists:
        raise HTTPException(
            status_code=422,
            detail={
                "type": "LOCKER_NOT_IN_PARTNER_SERVICE_AREA",
                "message": "Locker não está ativo na área de atendimento do parceiro.",
                "partner_id": partner_id,
                "locker_id": locker_id,
            },
        )

    allocation_row = db.execute(
        text(
            """
            SELECT id, order_id, locker_id, state
            FROM allocations
            WHERE id = :allocation_id
            FOR UPDATE
            """
        ),
        {"allocation_id": allocation_id},
    ).mappings().first()
    if not allocation_row:
        raise HTTPException(
            status_code=404,
            detail={
                "type": "ALLOCATION_NOT_FOUND",
                "message": "Allocation não encontrada.",
                "allocation_id": allocation_id,
            },
        )
    if str(allocation_row["locker_id"] or "") != locker_id:
        raise HTTPException(
            status_code=422,
            detail={
                "type": "ALLOCATION_LOCKER_MISMATCH",
                "message": "Allocation não pertence ao locker informado.",
                "allocation_id": allocation_id,
                "locker_id": locker_id,
            },
        )

    slot_row = db.execute(
        text(
            """
            SELECT id, slot_label, slot_size
            FROM locker_slots
            WHERE locker_id = :locker_id
              AND current_allocation_id = :allocation_id
            FOR UPDATE
            """
        ),
        {"locker_id": locker_id, "allocation_id": allocation_id},
    ).mappings().first()

    allocation_state = str(allocation_row["state"] or "").upper()
    if allocation_state == "PICKED_UP":
        if not slot_row:
            slot_row = db.execute(
                text(
                    """
                    SELECT id, slot_label, slot_size
                    FROM locker_slots
                    WHERE locker_id = :locker_id
                    ORDER BY updated_at DESC, id DESC
                    LIMIT 1
                    """
                ),
                {"locker_id": locker_id},
            ).mappings().first()
        pickup_row = db.execute(
            text(
                """
                SELECT id, status
                FROM pickups
                WHERE order_id = :order_id
                ORDER BY created_at DESC, id DESC
                LIMIT 1
                """
            ),
            {"order_id": str(allocation_row["order_id"])},
        ).mappings().first()
        order_row = db.execute(
            text("SELECT status, picked_up_at FROM orders WHERE id = :order_id"),
            {"order_id": str(allocation_row["order_id"])},
        ).mappings().first()
        _audit_ops(
            db=db,
            action="PARTNER_SLOT_PICKUP_CONFIRM",
            result="SUCCESS",
            correlation_id=corr_id,
            user_id=None,
            details={
                "partner_id": partner_id,
                "locker_id": locker_id,
                "allocation_id": allocation_id,
                "order_id": str(allocation_row["order_id"]),
                "idempotent": True,
            },
        )
        db.commit()
        return PartnerSlotAllocationPickupConfirmOut(
            ok=True,
            idempotent=True,
            partner_id=partner_id,
            locker_id=locker_id,
            allocation_id=allocation_id,
            order_id=str(allocation_row["order_id"]),
            pickup_id=(str(pickup_row["id"]) if pickup_row else None),
            slot_id=(str(slot_row["id"]) if slot_row else ""),
            slot_label=(str(slot_row["slot_label"]) if slot_row else ""),
            slot_size=(str(slot_row["slot_size"]) if slot_row else ""),
            allocation_state="PICKED_UP",
            pickup_status=(str(pickup_row["status"]) if pickup_row else None),
            order_status=(str((order_row or {}).get("status") or "PICKED_UP")),
            released_at=_to_iso_utc((order_row or {}).get("picked_up_at") or datetime.now(timezone.utc)),
        )

    if allocation_state not in {"RESERVED_PAID_PENDING_PICKUP", "OPENED_FOR_PICKUP"}:
        raise HTTPException(
            status_code=409,
            detail={
                "type": "ALLOCATION_STATE_NOT_PICKUP_READY",
                "message": "Allocation não está pronta para confirmação de retirada.",
                "allocation_id": allocation_id,
                "state": allocation_state,
            },
        )

    if not slot_row:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail={
                "type": "SLOT_ALLOCATION_LINK_BROKEN",
                "message": "Slot vinculado à allocation não foi encontrado no locker.",
                "allocation_id": allocation_id,
                "locker_id": locker_id,
            },
        )

    now = datetime.now(timezone.utc)
    pickup_row = db.execute(
        text(
            """
            SELECT id, status
            FROM pickups
            WHERE order_id = :order_id
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            FOR UPDATE
            """
        ),
        {"order_id": str(allocation_row["order_id"])},
    ).mappings().first()
    if pickup_row:
        pickup_status = str(pickup_row["status"] or "").upper()
        if pickup_status != "REDEEMED":
            db.execute(
                text(
                    """
                    UPDATE pickups
                    SET
                        status = 'REDEEMED',
                        lifecycle_stage = 'COMPLETED',
                        redeemed_at = COALESCE(redeemed_at, :now),
                        redeemed_via = 'OPERATOR',
                        item_removed_at = COALESCE(item_removed_at, :now),
                        door_closed_at = COALESCE(door_closed_at, :now),
                        current_token_id = NULL,
                        updated_at = :now
                    WHERE id = :pickup_id
                    """
                ),
                {"pickup_id": str(pickup_row["id"]), "now": now},
            )

    db.execute(
        text(
            """
            UPDATE orders
            SET
                status = 'PICKED_UP',
                picked_up_at = COALESCE(picked_up_at, :now),
                updated_at = :now
            WHERE id = :order_id
            """
        ),
        {"order_id": str(allocation_row["order_id"]), "now": now},
    )
    db.execute(
        text(
            """
            UPDATE allocations
            SET
                state = 'PICKED_UP',
                locked_until = NULL,
                updated_at = :now
            WHERE id = :allocation_id
            """
        ),
        {"allocation_id": allocation_id, "now": now},
    )
    db.execute(
        text(
            """
            UPDATE locker_slots
            SET
                status = 'AVAILABLE',
                occupied_since = NULL,
                current_allocation_id = NULL,
                last_opened_at = :now,
                updated_at = :now
            WHERE id = :slot_id
            """
        ),
        {"slot_id": str(slot_row["id"]), "now": now},
    )

    pickup_after = db.execute(
        text("SELECT id, status FROM pickups WHERE id = :pickup_id"),
        {"pickup_id": (str(pickup_row["id"]) if pickup_row else "")},
    ).mappings().first() if pickup_row else None
    order_after = db.execute(
        text("SELECT status, picked_up_at FROM orders WHERE id = :order_id"),
        {"order_id": str(allocation_row["order_id"])},
    ).mappings().first()
    db.commit()
    _audit_ops(
        db=db,
        action="PARTNER_SLOT_PICKUP_CONFIRM",
        result="SUCCESS",
        correlation_id=corr_id,
        user_id=None,
        details={
            "partner_id": partner_id,
            "locker_id": locker_id,
            "allocation_id": allocation_id,
            "order_id": str(allocation_row["order_id"]),
            "pickup_id": (str(pickup_after["id"]) if pickup_after else None),
            "idempotent": False,
        },
    )
    db.commit()

    return PartnerSlotAllocationPickupConfirmOut(
        ok=True,
        idempotent=False,
        partner_id=partner_id,
        locker_id=locker_id,
        allocation_id=allocation_id,
        order_id=str(allocation_row["order_id"]),
        pickup_id=(str(pickup_after["id"]) if pickup_after else None),
        slot_id=str(slot_row["id"]),
        slot_label=str(slot_row["slot_label"] or ""),
        slot_size=str(slot_row["slot_size"] or ""),
        allocation_state="PICKED_UP",
        pickup_status=(str(pickup_after["status"]) if pickup_after else None),
        order_status=str((order_after or {}).get("status") or "PICKED_UP"),
        released_at=_to_iso_utc((order_after or {}).get("picked_up_at") or now),
    )


@router.get("/ops/webhooks/metrics", response_model=PartnerWebhookOpsMetricsOut)
def get_partners_ops_webhook_metrics(
    partner_id: str | None = Query(default=None),
    from_: str | None = Query(default=None, alias="from"),
    to: str | None = Query(default=None),
    top_n: int = Query(default=5, ge=1, le=20),
    threshold_error_rate_pct: float = Query(default=5.0, ge=0, le=100),
    threshold_p95_latency_ms: float = Query(default=4000.0, ge=0, le=600000),
    threshold_backlog: int = Query(default=25, ge=0, le=100000),
    threshold_endpoint_error_rate_pct: float = Query(default=10.0, ge=0, le=100),
    threshold_endpoint_p95_latency_ms: float = Query(default=5000.0, ge=0, le=600000),
    threshold_endpoint_backlog: int = Query(default=10, ge=0, le=100000),
    threshold_dead_letter: int = Query(default=1, ge=0, le=100000),
    include_alerts: bool = Query(default=True),
    db: Session = Depends(get_db),
):
    dt_to = _parse_iso_datetime_utc_optional(to, field_name="to") or datetime.now(timezone.utc)
    dt_from = _parse_iso_datetime_utc_optional(from_, field_name="from") or (dt_to - timedelta(days=7))
    if dt_from > dt_to:
        raise HTTPException(
            status_code=422,
            detail={"type": "INVALID_DATE_RANGE", "message": "from deve ser <= to."},
        )

    where_parts = [
        "d.created_at >= :dt_from",
        "d.created_at <= :dt_to",
    ]
    params: dict[str, object] = {"dt_from": dt_from, "dt_to": dt_to, "top_n": int(top_n)}
    normalized_partner_id = str(partner_id or "").strip()
    if normalized_partner_id:
        where_parts.append("e.partner_id = :partner_id")
        params["partner_id"] = normalized_partner_id
    where_sql = " AND ".join(where_parts)

    total_row = db.execute(
        text(
            f"""
            SELECT
                COUNT(*)::int AS total_deliveries,
                COUNT(*) FILTER (WHERE d.status = 'DELIVERED')::int AS total_delivered,
                COUNT(*) FILTER (WHERE d.status = 'FAILED')::int AS total_failed,
                COUNT(*) FILTER (WHERE d.status = 'DEAD_LETTER')::int AS total_dead_letter,
                COUNT(*) FILTER (WHERE d.status IN ('PENDING', 'FAILED'))::int AS backlog_pending_failed,
                COALESCE(
                    ROUND(
                        (
                            (COUNT(*) FILTER (WHERE d.status IN ('FAILED', 'DEAD_LETTER')))::numeric
                            / NULLIF(COUNT(*)::numeric, 0)
                        ) * 100.0,
                        2
                    ),
                    0
                ) AS error_rate_pct,
                COALESCE(
                    ROUND(
                        AVG(
                            CASE
                                WHEN d.delivered_at IS NOT NULL
                                THEN EXTRACT(EPOCH FROM (d.delivered_at - d.created_at)) * 1000
                                ELSE NULL
                            END
                        )::numeric,
                        2
                    ),
                    0
                ) AS avg_latency_ms,
                COALESCE(
                    ROUND(
                        percentile_cont(0.95) WITHIN GROUP (
                            ORDER BY CASE
                                WHEN d.delivered_at IS NOT NULL
                                THEN EXTRACT(EPOCH FROM (d.delivered_at - d.created_at)) * 1000
                                ELSE NULL
                            END
                        )::numeric,
                        2
                    ),
                    0
                ) AS p95_latency_ms
            FROM partner_webhook_deliveries d
            JOIN partner_webhook_endpoints e ON e.id = d.endpoint_id
            WHERE {where_sql}
            """
        ),
        params,
    ).mappings().first() or {}

    daily_rows = db.execute(
        text(
            f"""
            SELECT
                DATE_TRUNC('day', d.created_at) AS day_ref,
                COUNT(*)::int AS total,
                COUNT(*) FILTER (WHERE d.status = 'DELIVERED')::int AS delivered,
                COUNT(*) FILTER (WHERE d.status = 'FAILED')::int AS failed,
                COUNT(*) FILTER (WHERE d.status = 'DEAD_LETTER')::int AS dead_letter,
                COUNT(*) FILTER (WHERE d.status IN ('PENDING', 'FAILED'))::int AS pending,
                COALESCE(
                    ROUND(
                        (
                            (COUNT(*) FILTER (WHERE d.status IN ('FAILED', 'DEAD_LETTER')))::numeric
                            / NULLIF(COUNT(*)::numeric, 0)
                        ) * 100.0,
                        2
                    ),
                    0
                ) AS error_rate_pct
            FROM partner_webhook_deliveries d
            JOIN partner_webhook_endpoints e ON e.id = d.endpoint_id
            WHERE {where_sql}
            GROUP BY DATE_TRUNC('day', d.created_at)
            ORDER BY DATE_TRUNC('day', d.created_at) ASC
            """
        ),
        params,
    ).mappings().all()

    top_partner_rows = db.execute(
        text(
            f"""
            SELECT
                e.partner_id AS partner_id,
                COUNT(*)::int AS total,
                COUNT(*) FILTER (WHERE d.status = 'FAILED')::int AS failed,
                COUNT(*) FILTER (WHERE d.status = 'DEAD_LETTER')::int AS dead_letter,
                COUNT(*) FILTER (WHERE d.status IN ('PENDING', 'FAILED'))::int AS pending,
                COALESCE(
                    ROUND(
                        (
                            (COUNT(*) FILTER (WHERE d.status IN ('FAILED', 'DEAD_LETTER')))::numeric
                            / NULLIF(COUNT(*)::numeric, 0)
                        ) * 100.0,
                        2
                    ),
                    0
                ) AS error_rate_pct,
                COALESCE(
                    ROUND(
                        AVG(
                            CASE
                                WHEN d.delivered_at IS NOT NULL
                                THEN EXTRACT(EPOCH FROM (d.delivered_at - d.created_at)) * 1000
                                ELSE NULL
                            END
                        )::numeric,
                        2
                    ),
                    0
                ) AS avg_latency_ms,
                COALESCE(
                    ROUND(
                        percentile_cont(0.95) WITHIN GROUP (
                            ORDER BY CASE
                                WHEN d.delivered_at IS NOT NULL
                                THEN EXTRACT(EPOCH FROM (d.delivered_at - d.created_at)) * 1000
                                ELSE NULL
                            END
                        )::numeric,
                        2
                    ),
                    0
                ) AS p95_latency_ms
            FROM partner_webhook_deliveries d
            JOIN partner_webhook_endpoints e ON e.id = d.endpoint_id
            WHERE {where_sql}
            GROUP BY e.partner_id
            ORDER BY total DESC, partner_id ASC
            LIMIT :top_n
            """
        ),
        params,
    ).mappings().all()

    top_endpoint_rows = db.execute(
        text(
            f"""
            SELECT
                d.endpoint_id AS endpoint_id,
                e.partner_id AS partner_id,
                e.url AS endpoint_url,
                COUNT(*)::int AS total,
                COUNT(*) FILTER (WHERE d.status = 'FAILED')::int AS failed,
                COUNT(*) FILTER (WHERE d.status = 'DEAD_LETTER')::int AS dead_letter,
                COUNT(*) FILTER (WHERE d.status IN ('PENDING', 'FAILED'))::int AS pending,
                COALESCE(
                    ROUND(
                        (
                            (COUNT(*) FILTER (WHERE d.status IN ('FAILED', 'DEAD_LETTER')))::numeric
                            / NULLIF(COUNT(*)::numeric, 0)
                        ) * 100.0,
                        2
                    ),
                    0
                ) AS error_rate_pct,
                COALESCE(
                    ROUND(
                        AVG(
                            CASE
                                WHEN d.delivered_at IS NOT NULL
                                THEN EXTRACT(EPOCH FROM (d.delivered_at - d.created_at)) * 1000
                                ELSE NULL
                            END
                        )::numeric,
                        2
                    ),
                    0
                ) AS avg_latency_ms,
                COALESCE(
                    ROUND(
                        percentile_cont(0.95) WITHIN GROUP (
                            ORDER BY CASE
                                WHEN d.delivered_at IS NOT NULL
                                THEN EXTRACT(EPOCH FROM (d.delivered_at - d.created_at)) * 1000
                                ELSE NULL
                            END
                        )::numeric,
                        2
                    ),
                    0
                ) AS p95_latency_ms
            FROM partner_webhook_deliveries d
            JOIN partner_webhook_endpoints e ON e.id = d.endpoint_id
            WHERE {where_sql}
            GROUP BY d.endpoint_id, e.partner_id, e.url
            ORDER BY total DESC, endpoint_id ASC
            LIMIT :top_n
            """
        ),
        params,
    ).mappings().all()

    total_deliveries = int(total_row.get("total_deliveries") or 0)
    total_delivered = int(total_row.get("total_delivered") or 0)
    total_failed = int(total_row.get("total_failed") or 0)
    total_dead_letter = int(total_row.get("total_dead_letter") or 0)
    backlog_pending_failed = int(total_row.get("backlog_pending_failed") or 0)
    error_rate_pct = float(total_row.get("error_rate_pct") or 0.0)
    avg_latency_ms = float(total_row.get("avg_latency_ms") or 0.0)
    p95_latency_ms = float(total_row.get("p95_latency_ms") or 0.0)

    daily = [
        PartnerWebhookOpsDailyOut(
            day=_to_iso_utc(row.get("day_ref")),
            total=int(row.get("total") or 0),
            delivered=int(row.get("delivered") or 0),
            failed=int(row.get("failed") or 0),
            dead_letter=int(row.get("dead_letter") or 0),
            pending=int(row.get("pending") or 0),
            error_rate_pct=float(row.get("error_rate_pct") or 0.0),
        )
        for row in daily_rows
    ]
    top_partners = [
        PartnerWebhookOpsTopPartnerOut(
            partner_id=str(row.get("partner_id") or ""),
            total=int(row.get("total") or 0),
            failed=int(row.get("failed") or 0),
            dead_letter=int(row.get("dead_letter") or 0),
            pending=int(row.get("pending") or 0),
            error_rate_pct=float(row.get("error_rate_pct") or 0.0),
            avg_latency_ms=float(row.get("avg_latency_ms") or 0.0),
            p95_latency_ms=float(row.get("p95_latency_ms") or 0.0),
        )
        for row in top_partner_rows
    ]
    top_endpoints = [
        PartnerWebhookOpsTopEndpointOut(
            endpoint_id=str(row.get("endpoint_id") or ""),
            partner_id=str(row.get("partner_id") or ""),
            endpoint_url=str(row.get("endpoint_url") or ""),
            total=int(row.get("total") or 0),
            failed=int(row.get("failed") or 0),
            dead_letter=int(row.get("dead_letter") or 0),
            pending=int(row.get("pending") or 0),
            error_rate_pct=float(row.get("error_rate_pct") or 0.0),
            avg_latency_ms=float(row.get("avg_latency_ms") or 0.0),
            p95_latency_ms=float(row.get("p95_latency_ms") or 0.0),
        )
        for row in top_endpoint_rows
    ]

    alerts: list[PartnerWebhookOpsAlertOut] = []
    if include_alerts:
        if error_rate_pct >= threshold_error_rate_pct:
            alerts.append(
                PartnerWebhookOpsAlertOut(
                    code="WEBHOOK_ERROR_RATE_HIGH",
                    severity="HIGH",
                    title="Taxa de erro global acima do limite",
                    message="Taxa de erro de webhook acima do limiar operacional definido.",
                    value=error_rate_pct,
                    threshold=float(threshold_error_rate_pct),
                )
            )
        if p95_latency_ms >= threshold_p95_latency_ms:
            alerts.append(
                PartnerWebhookOpsAlertOut(
                    code="WEBHOOK_P95_LATENCY_HIGH",
                    severity="MEDIUM",
                    title="Latência P95 global acima do limite",
                    message="Latência P95 de entrega de webhook acima do limiar operacional.",
                    value=p95_latency_ms,
                    threshold=float(threshold_p95_latency_ms),
                )
            )
        if backlog_pending_failed >= threshold_backlog:
            alerts.append(
                PartnerWebhookOpsAlertOut(
                    code="WEBHOOK_BACKLOG_HIGH",
                    severity="HIGH",
                    title="Backlog de webhook acima do limite",
                    message="Volume de eventos pendentes/falhos acima do limiar operacional.",
                    value=float(backlog_pending_failed),
                    threshold=float(threshold_backlog),
                )
            )
        if total_dead_letter >= threshold_dead_letter:
            alerts.append(
                PartnerWebhookOpsAlertOut(
                    code="WEBHOOK_DEAD_LETTER_DETECTED",
                    severity="HIGH",
                    title="Dead-letter detectado",
                    message="Existem eventos em dead-letter na janela consultada.",
                    value=float(total_dead_letter),
                    threshold=float(threshold_dead_letter),
                )
            )

        for endpoint in top_endpoints:
            if endpoint.error_rate_pct >= threshold_endpoint_error_rate_pct:
                alerts.append(
                    PartnerWebhookOpsAlertOut(
                        code="WEBHOOK_ENDPOINT_ERROR_RATE_HIGH",
                        severity="HIGH",
                        title="Endpoint com taxa de erro elevada",
                        message="Endpoint com taxa de erro acima do limiar por endpoint.",
                        value=endpoint.error_rate_pct,
                        threshold=float(threshold_endpoint_error_rate_pct),
                        partner_id=endpoint.partner_id,
                        endpoint_id=endpoint.endpoint_id,
                        endpoint_url=endpoint.endpoint_url,
                    )
                )
            if endpoint.p95_latency_ms >= threshold_endpoint_p95_latency_ms:
                alerts.append(
                    PartnerWebhookOpsAlertOut(
                        code="WEBHOOK_ENDPOINT_P95_LATENCY_HIGH",
                        severity="MEDIUM",
                        title="Endpoint com latência P95 elevada",
                        message="Endpoint com latência acima do limiar por endpoint.",
                        value=endpoint.p95_latency_ms,
                        threshold=float(threshold_endpoint_p95_latency_ms),
                        partner_id=endpoint.partner_id,
                        endpoint_id=endpoint.endpoint_id,
                        endpoint_url=endpoint.endpoint_url,
                    )
                )
            if endpoint.pending >= threshold_endpoint_backlog:
                alerts.append(
                    PartnerWebhookOpsAlertOut(
                        code="WEBHOOK_ENDPOINT_BACKLOG_HIGH",
                        severity="HIGH",
                        title="Endpoint com backlog elevado",
                        message="Endpoint com pendências/falhas acima do limiar por endpoint.",
                        value=float(endpoint.pending),
                        threshold=float(threshold_endpoint_backlog),
                        partner_id=endpoint.partner_id,
                        endpoint_id=endpoint.endpoint_id,
                        endpoint_url=endpoint.endpoint_url,
                    )
                )

    return PartnerWebhookOpsMetricsOut(
        ok=True,
        **{
            "from": _to_iso_utc(dt_from),
            "to": _to_iso_utc(dt_to),
        },
        timezone_ref="UTC",
        partner_id=(normalized_partner_id or None),
        total_deliveries=total_deliveries,
        total_delivered=total_delivered,
        total_failed=total_failed,
        total_dead_letter=total_dead_letter,
        backlog_pending_failed=backlog_pending_failed,
        error_rate_pct=error_rate_pct,
        avg_latency_ms=avg_latency_ms,
        p95_latency_ms=p95_latency_ms,
        daily=daily,
        top_partners=top_partners,
        top_endpoints=top_endpoints,
        alerts=alerts,
    )


@router.get("/ops/pickup-confirm/metrics", response_model=PartnerPickupConfirmMetricsOut)
def get_partners_ops_pickup_confirm_metrics(
    period_from: str | None = Query(default=None),
    period_to: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    dt_to = _parse_iso_datetime_utc_optional(period_to, field_name="period_to") or datetime.now(timezone.utc)
    dt_from = _parse_iso_datetime_utc_optional(period_from, field_name="period_from") or (dt_to - timedelta(days=7))
    if dt_from > dt_to:
        raise HTTPException(
            status_code=422,
            detail={"type": "INVALID_DATE_RANGE", "message": "period_from deve ser <= period_to."},
        )

    rows = db.execute(
        text(
            """
            SELECT result, details_json
            FROM ops_action_audit
            WHERE action = 'PARTNER_SLOT_PICKUP_CONFIRM'
              AND created_at >= :dt_from
              AND created_at <= :dt_to
            """
        ),
        {"dt_from": dt_from, "dt_to": dt_to},
    ).mappings().all()
    total_calls = len(rows)
    total_success = 0
    total_error = 0
    idempotent_calls = 0
    for row in rows:
        result = str(row.get("result") or "").upper()
        details = _json_load_dict(row.get("details_json"))
        if result == "SUCCESS":
            total_success += 1
        else:
            total_error += 1
        if bool(details.get("idempotent")):
            idempotent_calls += 1
    effective_calls = max(total_success - idempotent_calls, 0)
    success_rate_pct = round((total_success / total_calls) * 100.0, 2) if total_calls > 0 else 0.0
    idempotent_rate_pct = round((idempotent_calls / total_success) * 100.0, 2) if total_success > 0 else 0.0
    return PartnerPickupConfirmMetricsOut(
        ok=True,
        period_from=_to_iso_utc(dt_from),
        period_to=_to_iso_utc(dt_to),
        total_calls=total_calls,
        total_success=total_success,
        total_error=total_error,
        success_rate_pct=success_rate_pct,
        idempotent_calls=idempotent_calls,
        effective_calls=effective_calls,
        idempotent_rate_pct=idempotent_rate_pct,
    )


def _calc_pickup_confirm_window_metrics(rows: list[dict]) -> PartnerPickupConfirmMetricsCompareWindowOut:
    total_calls = len(rows)
    total_success = 0
    total_error = 0
    idempotent_calls = 0
    for row in rows:
        result = str(row.get("result") or "").upper()
        details = _json_load_dict(row.get("details_json"))
        if result == "SUCCESS":
            total_success += 1
        else:
            total_error += 1
        if bool(details.get("idempotent")):
            idempotent_calls += 1
    effective_calls = max(total_success - idempotent_calls, 0)
    success_rate_pct = round((total_success / total_calls) * 100.0, 2) if total_calls > 0 else 0.0
    idempotent_rate_pct = round((idempotent_calls / total_success) * 100.0, 2) if total_success > 0 else 0.0
    return PartnerPickupConfirmMetricsCompareWindowOut(
        total_calls=total_calls,
        total_success=total_success,
        total_error=total_error,
        success_rate_pct=success_rate_pct,
        idempotent_calls=idempotent_calls,
        effective_calls=effective_calls,
        idempotent_rate_pct=idempotent_rate_pct,
    )


@router.get("/ops/pickup-confirm/metrics/compare", response_model=PartnerPickupConfirmMetricsCompareOut)
def get_partners_ops_pickup_confirm_metrics_compare(
    period_from: str | None = Query(default=None),
    period_to: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    current_to = _parse_iso_datetime_utc_optional(period_to, field_name="period_to") or datetime.now(timezone.utc)
    current_from = _parse_iso_datetime_utc_optional(period_from, field_name="period_from") or (current_to - timedelta(days=7))
    if current_from > current_to:
        raise HTTPException(
            status_code=422,
            detail={"type": "INVALID_DATE_RANGE", "message": "period_from deve ser <= period_to."},
        )

    window_span = current_to - current_from
    previous_to = current_from
    previous_from = previous_to - window_span

    current_rows = db.execute(
        text(
            """
            SELECT result, details_json
            FROM ops_action_audit
            WHERE action = 'PARTNER_SLOT_PICKUP_CONFIRM'
              AND created_at >= :dt_from
              AND created_at <= :dt_to
            """
        ),
        {"dt_from": current_from, "dt_to": current_to},
    ).mappings().all()
    previous_rows = db.execute(
        text(
            """
            SELECT result, details_json
            FROM ops_action_audit
            WHERE action = 'PARTNER_SLOT_PICKUP_CONFIRM'
              AND created_at >= :dt_from
              AND created_at <= :dt_to
            """
        ),
        {"dt_from": previous_from, "dt_to": previous_to},
    ).mappings().all()

    current = _calc_pickup_confirm_window_metrics(current_rows)
    previous = _calc_pickup_confirm_window_metrics(previous_rows)

    return PartnerPickupConfirmMetricsCompareOut(
        ok=True,
        period_from=_to_iso_utc(current_from),
        period_to=_to_iso_utc(current_to),
        previous_from=_to_iso_utc(previous_from),
        previous_to=_to_iso_utc(previous_to),
        current=current,
        previous=previous,
        delta_calls_pct=_safe_delta_pct(current.total_calls, previous.total_calls),
        delta_effective_calls_pct=_safe_delta_pct(current.effective_calls, previous.effective_calls),
        delta_success_rate_pct=round(current.success_rate_pct - previous.success_rate_pct, 2),
    )


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
        details = _json_load_dict(row.details_json, default={})
        row_partner_id = _extract_partner_id(details)
        if partner_id and str(row_partner_id or "").strip() != str(partner_id).strip():
            continue
        filtered.append(row)

    sliced = filtered[offset : offset + limit]
    items = []
    for row in sliced:
        details = _json_load_dict(row.details_json, default={})
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
        timezone_ref="UTC",
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
        timezone_ref="UTC",
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
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
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

    current_rows = _load_ops_audit_rows_for_compare(
        db,
        window_from=current_from,
        window_to=current_to,
        partner_id=partner_id,
        sort_order=sort_order,
    )
    previous_rows = _load_ops_audit_rows_for_compare(
        db,
        window_from=previous_from,
        window_to=previous_to,
        partner_id=partner_id,
        sort_order=sort_order,
    )

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
        timezone_ref="UTC",
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
