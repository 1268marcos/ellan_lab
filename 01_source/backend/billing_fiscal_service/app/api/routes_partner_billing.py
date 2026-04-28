from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.schemas.partner_billing_schema import (
    PartnerB2BInvoiceOut,
    PartnerBillingCycleOut,
    PartnerBillingDisputeIn,
    PartnerCreditNoteOut,
    PartnerDisputeHistoryOut,
    PartnerBillingLineItemOut,
)
from app.services.partner_billing_cycle_service import compute_cycle_once, open_cycle_dispute
from app.services.partner_billing_utilization_service import recompute_daily_utilization_snapshot

router = APIRouter(prefix="/v1/partners", tags=["partner-billing"])

VALID_CYCLE_STATUS = {
    "OPEN",
    "COMPUTING",
    "REVIEW",
    "APPROVED",
    "INVOICED",
    "PAID",
    "DISPUTED",
    "CANCELLED",
}
VALID_LINE_TYPES = {
    "BASE_FEE",
    "DELIVERY_FEE",
    "PICKUP_FEE",
    "STORAGE_DAY_FEE",
    "OVERAGE_FEE",
    "SLA_PENALTY",
    "TAX",
    "DISCOUNT",
    "CREDIT_NOTE",
    "ADJUSTMENT",
}
VALID_INVOICE_STATUS = {"DRAFT", "ISSUED", "SENT", "VIEWED", "PAID", "OVERDUE", "DISPUTED", "CANCELLED"}
VALID_INVOICE_DOCUMENT_TYPES = {"INVOICE", "NFS_E", "NFE_55", "NFC_E_65", "BOLETO", "INVOICE_PDF"}
VALID_CREDIT_NOTE_STATUS = {"PENDING", "APPROVED", "APPLIED", "REFUNDED", "EXPIRED", "CANCELLED"}
VALID_CREDIT_NOTE_REASON_CODES = {
    "SLA_BREACH",
    "HARDWARE_DOWNTIME",
    "COMMERCIAL_ADJUSTMENT",
    "DUPLICATE",
    "TAX_ADJUSTMENT",
    "OTHER",
}
VALID_SORT_ORDER = {"ASC", "DESC"}
CYCLE_SORT_FIELDS = {
    "period_start": "period_start",
    "period_end": "period_end",
    "created_at": "created_at",
    "updated_at": "updated_at",
    "total_amount_cents": "total_amount_cents",
    "status": "status",
}
LINE_ITEM_SORT_FIELDS = {
    "id": "id",
    "created_at": "created_at",
    "line_type": "line_type",
    "total_cents": "total_cents",
    "quantity": "quantity",
}
INVOICE_SORT_FIELDS = {
    "created_at": "created_at",
    "updated_at": "updated_at",
    "due_date": "due_date",
    "amount_cents": "amount_cents",
    "status": "status",
}
CREDIT_NOTE_SORT_FIELDS = {
    "created_at": "created_at",
    "updated_at": "updated_at",
    "amount_cents": "amount_cents",
    "status": "status",
    "reason_code": "reason_code",
}
DISPUTE_SORT_FIELDS = {
    "opened_at": "opened_at",
    "status": "status",
}
UTILIZATION_SORT_FIELDS = {
    "snapshot_date": "snapshot_date",
    "partner_id": "partner_id",
    "locker_id": "locker_id",
    "difference_hours": "difference_hours",
    "difference_pct": "difference_pct",
    "divergence_status": "divergence_status",
    "updated_at": "updated_at",
}
VALID_UTILIZATION_STATUS = {"OK", "UNDER_BILLED", "OVER_BILLED", "MISSING_BILLING"}


def validate_internal_token(internal_token: str = Header(..., alias="X-Internal-Token")):
    if internal_token != settings.internal_token:
        raise HTTPException(status_code=403, detail="Invalid internal token")


def _api_error(status_code: int, code: str, message: str, context: dict | None = None) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={
            "ok": False,
            "error": {
                "code": code,
                "message": message,
                "context": context or {},
            },
        },
    )


def _row_to_dict(row: dict) -> dict:
    return {
        k: (v.isoformat() if hasattr(v, "isoformat") and v is not None else v)
        for k, v in dict(row).items()
    }


def _normalize_enum(
    raw_value: str | None,
    allowed: set[str],
    *,
    param_name: str,
    error_code: str,
) -> str | None:
    if raw_value is None:
        return None
    normalized = raw_value.strip().upper()
    if normalized not in allowed:
        raise _api_error(
            422,
            error_code,
            f"Invalid {param_name}",
            {"param": param_name, "value": raw_value, "allowed": sorted(allowed)},
        )
    return normalized


def _resolve_sorting(
    *,
    sort_by: str,
    sort_order: str,
    allowed_fields: dict[str, str],
    default_field: str,
) -> tuple[str, str]:
    field_key = (sort_by or default_field).strip().lower()
    if field_key not in allowed_fields:
        raise _api_error(
            422,
            "INVALID_SORT_FIELD",
            "Invalid sort_by",
            {"sort_by": sort_by, "allowed": sorted(allowed_fields.keys())},
        )
    order = (sort_order or "DESC").strip().upper()
    if order not in VALID_SORT_ORDER:
        raise _api_error(
            422,
            "INVALID_SORT_ORDER",
            "Invalid sort_order",
            {"sort_order": sort_order, "allowed": sorted(VALID_SORT_ORDER)},
        )
    return allowed_fields[field_key], order


@router.get("/{partner_id}/billing/cycles")
def list_partner_cycles(
    partner_id: str,
    year: int | None = Query(default=None, ge=2020, le=2100),
    status: str | None = Query(default=None),
    country_code: str | None = Query(default=None, min_length=2, max_length=2),
    jurisdiction_code: str | None = Query(default=None, max_length=32),
    from_date: str | None = Query(default=None),
    to_date: str | None = Query(default=None),
    sort_by: str = Query(default="period_start"),
    sort_order: str = Query(default="DESC"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: None = Depends(validate_internal_token),
):
    clauses = ["partner_id = :partner_id"]
    params: dict[str, object] = {"partner_id": partner_id}
    if year is not None:
        clauses.append("EXTRACT(YEAR FROM period_start) = :year")
        params["year"] = int(year)
    status_norm = _normalize_enum(
        status,
        VALID_CYCLE_STATUS,
        param_name="status",
        error_code="INVALID_CYCLE_STATUS",
    )
    if status_norm:
        clauses.append("status = :status")
        params["status"] = status_norm
    if country_code:
        clauses.append("country_code = :country_code")
        params["country_code"] = country_code.strip().upper()
    if jurisdiction_code:
        clauses.append("jurisdiction_code = :jurisdiction_code")
        params["jurisdiction_code"] = jurisdiction_code.strip().upper()
    if from_date:
        clauses.append("period_start >= :from_date")
        params["from_date"] = from_date
    if to_date:
        clauses.append("period_end <= :to_date")
        params["to_date"] = to_date
    params["limit"] = int(limit)
    params["offset"] = int(offset)
    sort_field, sort_direction = _resolve_sorting(
        sort_by=sort_by,
        sort_order=sort_order,
        allowed_fields=CYCLE_SORT_FIELDS,
        default_field="period_start",
    )

    rows = db.execute(
        text(
            f"""
            SELECT id, partner_id, status, currency, country_code, jurisdiction_code, period_timezone,
                   period_start, period_end, total_amount_cents, dedupe_key, computed_at
            FROM partner_billing_cycles
            WHERE {' AND '.join(clauses)}
            ORDER BY {sort_field} {sort_direction}, created_at DESC
            LIMIT :limit OFFSET :offset
            """
        ),
        params,
    ).mappings().all()
    count_row = db.execute(
        text(f"SELECT COUNT(*) FROM partner_billing_cycles WHERE {' AND '.join(clauses)}"),
        {k: v for k, v in params.items() if k not in ("limit", "offset")},
    ).fetchone()
    items = [PartnerBillingCycleOut(**_row_to_dict(r)) for r in rows]
    return {
        "count": len(items),
        "total": int(count_row[0] if count_row else 0),
        "limit": limit,
        "offset": offset,
        "sort_by": sort_by,
        "sort_order": sort_direction,
        "items": items,
    }


@router.get("/{partner_id}/billing/cycles/{cycle_id}/line-items")
def list_cycle_line_items(
    partner_id: str,
    cycle_id: str,
    line_type: str | None = Query(default=None),
    country_code: str | None = Query(default=None, min_length=2, max_length=2),
    jurisdiction_code: str | None = Query(default=None, max_length=32),
    sort_by: str = Query(default="id"),
    sort_order: str = Query(default="ASC"),
    limit: int = Query(default=200, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: None = Depends(validate_internal_token),
):
    clauses = ["partner_id = :partner_id", "cycle_id = :cycle_id"]
    params: dict[str, object] = {"partner_id": partner_id, "cycle_id": cycle_id, "limit": int(limit), "offset": int(offset)}
    line_type_norm = _normalize_enum(
        line_type,
        VALID_LINE_TYPES,
        param_name="line_type",
        error_code="INVALID_LINE_TYPE",
    )
    if line_type_norm:
        clauses.append("line_type = :line_type")
        params["line_type"] = line_type_norm
    if country_code:
        clauses.append("country_code = :country_code")
        params["country_code"] = country_code.strip().upper()
    if jurisdiction_code:
        clauses.append("jurisdiction_code = :jurisdiction_code")
        params["jurisdiction_code"] = jurisdiction_code.strip().upper()
    sort_field, sort_direction = _resolve_sorting(
        sort_by=sort_by,
        sort_order=sort_order,
        allowed_fields=LINE_ITEM_SORT_FIELDS,
        default_field="id",
    )

    rows = db.execute(
        text(
            f"""
            SELECT id, cycle_id, partner_id, line_type, description, quantity::text, unit_price_cents,
                   total_cents, currency, country_code, jurisdiction_code, dedupe_key, created_at
            FROM partner_billing_line_items
            WHERE {' AND '.join(clauses)}
            ORDER BY {sort_field} {sort_direction}, id ASC
            LIMIT :limit OFFSET :offset
            """
        ),
        params,
    ).mappings().all()
    count_row = db.execute(
        text(f"SELECT COUNT(*) FROM partner_billing_line_items WHERE {' AND '.join(clauses)}"),
        {k: v for k, v in params.items() if k not in ("limit", "offset")},
    ).fetchone()
    items = [PartnerBillingLineItemOut(**_row_to_dict(r)) for r in rows]
    return {
        "count": len(items),
        "total": int(count_row[0] if count_row else 0),
        "limit": limit,
        "offset": offset,
        "sort_by": sort_by,
        "sort_order": sort_direction,
        "items": items,
    }


@router.get("/{partner_id}/invoices")
def list_partner_b2b_invoices(
    partner_id: str,
    status: str | None = Query(default=None),
    from_date: str | None = Query(default=None),
    to_date: str | None = Query(default=None),
    country_code: str | None = Query(default=None, min_length=2, max_length=2),
    jurisdiction_code: str | None = Query(default=None, max_length=32),
    document_type: str | None = Query(default=None),
    sort_by: str = Query(default="created_at"),
    sort_order: str = Query(default="DESC"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: None = Depends(validate_internal_token),
):
    clauses = ["partner_id = :partner_id"]
    params: dict[str, object] = {"partner_id": partner_id}
    status_norm = _normalize_enum(
        status,
        VALID_INVOICE_STATUS,
        param_name="status",
        error_code="INVALID_INVOICE_STATUS",
    )
    if status_norm:
        clauses.append("status = :status")
        params["status"] = status_norm
    if from_date:
        clauses.append("created_at::date >= :from_date")
        params["from_date"] = from_date
    if to_date:
        clauses.append("created_at::date <= :to_date")
        params["to_date"] = to_date
    if country_code:
        clauses.append("country_code = :country_code")
        params["country_code"] = country_code.strip().upper()
    if jurisdiction_code:
        clauses.append("jurisdiction_code = :jurisdiction_code")
        params["jurisdiction_code"] = jurisdiction_code.strip().upper()
    document_type_norm = _normalize_enum(
        document_type,
        VALID_INVOICE_DOCUMENT_TYPES,
        param_name="document_type",
        error_code="INVALID_DOCUMENT_TYPE",
    )
    if document_type_norm:
        clauses.append("document_type = :document_type")
        params["document_type"] = document_type_norm
    params["limit"] = int(limit)
    params["offset"] = int(offset)
    sort_field, sort_direction = _resolve_sorting(
        sort_by=sort_by,
        sort_order=sort_order,
        allowed_fields=INVOICE_SORT_FIELDS,
        default_field="created_at",
    )

    rows = db.execute(
        text(
            f"""
            SELECT id, cycle_id, partner_id, status, document_type, amount_cents, tax_cents, currency,
                   country_code, jurisdiction_code, timezone, due_date, dedupe_key, created_at
            FROM partner_b2b_invoices
            WHERE {' AND '.join(clauses)}
            ORDER BY {sort_field} {sort_direction}, created_at DESC
            LIMIT :limit OFFSET :offset
            """
        ),
        params,
    ).mappings().all()
    count_row = db.execute(
        text(f"SELECT COUNT(*) FROM partner_b2b_invoices WHERE {' AND '.join(clauses)}"),
        {k: v for k, v in params.items() if k not in ("limit", "offset")},
    ).fetchone()
    items = [PartnerB2BInvoiceOut(**_row_to_dict(r)) for r in rows]
    return {
        "count": len(items),
        "total": int(count_row[0] if count_row else 0),
        "limit": limit,
        "offset": offset,
        "sort_by": sort_by,
        "sort_order": sort_direction,
        "items": items,
    }


@router.get("/{partner_id}/credit-notes")
def list_partner_credit_notes(
    partner_id: str,
    status: str | None = Query(default=None),
    reason_code: str | None = Query(default=None),
    country_code: str | None = Query(default=None, min_length=2, max_length=2),
    jurisdiction_code: str | None = Query(default=None, max_length=32),
    sort_by: str = Query(default="created_at"),
    sort_order: str = Query(default="DESC"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: None = Depends(validate_internal_token),
):
    clauses = ["partner_id = :partner_id"]
    params: dict[str, object] = {"partner_id": partner_id, "limit": int(limit), "offset": int(offset)}
    status_norm = _normalize_enum(
        status,
        VALID_CREDIT_NOTE_STATUS,
        param_name="status",
        error_code="INVALID_CREDIT_NOTE_STATUS",
    )
    if status_norm:
        clauses.append("status = :status")
        params["status"] = status_norm
    reason_code_norm = _normalize_enum(
        reason_code,
        VALID_CREDIT_NOTE_REASON_CODES,
        param_name="reason_code",
        error_code="INVALID_CREDIT_NOTE_REASON_CODE",
    )
    if reason_code_norm:
        clauses.append("reason_code = :reason_code")
        params["reason_code"] = reason_code_norm
    if country_code:
        clauses.append("country_code = :country_code")
        params["country_code"] = country_code.strip().upper()
    if jurisdiction_code:
        clauses.append("jurisdiction_code = :jurisdiction_code")
        params["jurisdiction_code"] = jurisdiction_code.strip().upper()
    sort_field, sort_direction = _resolve_sorting(
        sort_by=sort_by,
        sort_order=sort_order,
        allowed_fields=CREDIT_NOTE_SORT_FIELDS,
        default_field="created_at",
    )

    rows = db.execute(
        text(
            f"""
            SELECT id, partner_id, original_invoice_id, cycle_id, reason_code, amount_cents, currency,
                   country_code, jurisdiction_code, timezone, status, dispute_ref, dedupe_key, created_at
            FROM partner_credit_notes
            WHERE {' AND '.join(clauses)}
            ORDER BY {sort_field} {sort_direction}, created_at DESC
            LIMIT :limit OFFSET :offset
            """
        ),
        params,
    ).mappings().all()
    count_row = db.execute(
        text(f"SELECT COUNT(*) FROM partner_credit_notes WHERE {' AND '.join(clauses)}"),
        {k: v for k, v in params.items() if k not in ("limit", "offset")},
    ).fetchone()
    items = [PartnerCreditNoteOut(**_row_to_dict(r)) for r in rows]
    return {
        "count": len(items),
        "total": int(count_row[0] if count_row else 0),
        "limit": limit,
        "offset": offset,
        "sort_by": sort_by,
        "sort_order": sort_direction,
        "items": items,
    }


@router.get("/{partner_id}/billing/disputes")
def list_partner_disputes_history(
    partner_id: str,
    status: str | None = Query(default=None),
    from_date: str | None = Query(default=None),
    to_date: str | None = Query(default=None),
    country_code: str | None = Query(default=None, min_length=2, max_length=2),
    jurisdiction_code: str | None = Query(default=None, max_length=32),
    sort_by: str = Query(default="opened_at"),
    sort_order: str = Query(default="DESC"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: None = Depends(validate_internal_token),
):
    clauses = ["partner_id = :partner_id", "status = 'DISPUTED'"]
    params: dict[str, object] = {"partner_id": partner_id, "limit": int(limit), "offset": int(offset)}
    if status:
        status_norm = _normalize_enum(
            status,
            VALID_CYCLE_STATUS,
            param_name="status",
            error_code="INVALID_CYCLE_STATUS",
        )
        clauses.append("status = :status")
        params["status"] = status_norm
    if from_date:
        clauses.append("updated_at::date >= :from_date")
        params["from_date"] = from_date
    if to_date:
        clauses.append("updated_at::date <= :to_date")
        params["to_date"] = to_date
    if country_code:
        clauses.append("country_code = :country_code")
        params["country_code"] = country_code.strip().upper()
    if jurisdiction_code:
        clauses.append("jurisdiction_code = :jurisdiction_code")
        params["jurisdiction_code"] = jurisdiction_code.strip().upper()
    sort_field, sort_direction = _resolve_sorting(
        sort_by=sort_by,
        sort_order=sort_order,
        allowed_fields=DISPUTE_SORT_FIELDS,
        default_field="opened_at",
    )

    rows = db.execute(
        text(
            f"""
            SELECT id AS cycle_id, partner_id, 'CYCLE' AS dispute_scope, dispute_reason, status,
                   country_code, jurisdiction_code, COALESCE(updated_at, created_at) AS opened_at,
                   jsonb_build_object('dedupe_key', dedupe_key) AS metadata
            FROM partner_billing_cycles
            WHERE {' AND '.join(clauses)}
            ORDER BY {sort_field} {sort_direction}, opened_at DESC
            LIMIT :limit OFFSET :offset
            """
        ),
        params,
    ).mappings().all()
    count_row = db.execute(
        text(f"SELECT COUNT(*) FROM partner_billing_cycles WHERE {' AND '.join(clauses)}"),
        {k: v for k, v in params.items() if k not in ("limit", "offset")},
    ).fetchone()
    items = [PartnerDisputeHistoryOut(**_row_to_dict(r)) for r in rows]
    return {
        "count": len(items),
        "total": int(count_row[0] if count_row else 0),
        "limit": limit,
        "offset": offset,
        "sort_by": sort_by,
        "sort_order": sort_direction,
        "items": items,
    }


@router.post("/{partner_id}/billing/cycles/{cycle_id}/compute")
def compute_partner_cycle(
    partner_id: str,
    cycle_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(validate_internal_token),
):
    owner = db.execute(
        text("SELECT partner_id FROM partner_billing_cycles WHERE id = :cycle_id"),
        {"cycle_id": cycle_id},
    ).scalar_one_or_none()
    if owner is None:
        raise _api_error(404, "CYCLE_NOT_FOUND", "Cycle not found", {"cycle_id": cycle_id})
    if str(owner) != str(partner_id):
        raise _api_error(
            400,
            "PARTNER_CYCLE_MISMATCH",
            "Cycle does not belong to partner",
            {"cycle_id": cycle_id, "partner_id": partner_id},
        )

    result = compute_cycle_once(db, cycle_id)
    if result is None:
        raise _api_error(
            409,
            "CYCLE_NOT_ELIGIBLE",
            "Cycle not eligible or claim not acquired",
            {"cycle_id": cycle_id},
        )
    return {"ok": True, **result}


@router.post("/{partner_id}/billing/cycles/{cycle_id}/dispute")
def create_cycle_dispute(
    partner_id: str,
    cycle_id: str,
    body: PartnerBillingDisputeIn,
    db: Session = Depends(get_db),
    _: None = Depends(validate_internal_token),
):
    owner = db.execute(
        text("SELECT partner_id FROM partner_billing_cycles WHERE id = :cycle_id"),
        {"cycle_id": cycle_id},
    ).scalar_one_or_none()
    if owner is None:
        raise _api_error(404, "CYCLE_NOT_FOUND", "Cycle not found", {"cycle_id": cycle_id})
    if str(owner) != str(partner_id):
        raise _api_error(
            400,
            "PARTNER_CYCLE_MISMATCH",
            "Cycle does not belong to partner",
            {"cycle_id": cycle_id, "partner_id": partner_id},
        )

    try:
        dispute = open_cycle_dispute(db, cycle_id, reason=body.reason)
    except ValueError as exc:
        raise _api_error(400, "DISPUTE_INVALID_REQUEST", str(exc), {"cycle_id": cycle_id}) from exc
    return {"ok": True, "dispute": dispute}


@router.get("/ops/utilization-divergences")
def list_utilization_divergences(
    snapshot_date: str | None = Query(default=None),
    from_date: str | None = Query(default=None),
    to_date: str | None = Query(default=None),
    partner_id: str | None = Query(default=None),
    locker_id: str | None = Query(default=None),
    country_code: str | None = Query(default=None, min_length=2, max_length=2),
    jurisdiction_code: str | None = Query(default=None, max_length=32),
    divergence_status: str | None = Query(default=None),
    sort_by: str = Query(default="snapshot_date"),
    sort_order: str = Query(default="DESC"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: None = Depends(validate_internal_token),
):
    clauses = ["1=1"]
    params: dict[str, object] = {"limit": int(limit), "offset": int(offset)}
    if snapshot_date:
        clauses.append("snapshot_date = :snapshot_date")
        params["snapshot_date"] = snapshot_date
    if from_date:
        clauses.append("snapshot_date >= :from_date")
        params["from_date"] = from_date
    if to_date:
        clauses.append("snapshot_date <= :to_date")
        params["to_date"] = to_date
    if partner_id:
        clauses.append("partner_id = :partner_id")
        params["partner_id"] = partner_id
    if locker_id:
        clauses.append("locker_id = :locker_id")
        params["locker_id"] = locker_id
    if country_code:
        clauses.append("country_code = :country_code")
        params["country_code"] = country_code.strip().upper()
    if jurisdiction_code:
        clauses.append("jurisdiction_code = :jurisdiction_code")
        params["jurisdiction_code"] = jurisdiction_code.strip().upper()
    status_norm = _normalize_enum(
        divergence_status,
        VALID_UTILIZATION_STATUS,
        param_name="divergence_status",
        error_code="INVALID_UTILIZATION_STATUS",
    )
    if status_norm:
        clauses.append("divergence_status = :divergence_status")
        params["divergence_status"] = status_norm
    sort_field, sort_direction = _resolve_sorting(
        sort_by=sort_by,
        sort_order=sort_order,
        allowed_fields=UTILIZATION_SORT_FIELDS,
        default_field="snapshot_date",
    )

    rows = db.execute(
        text(
            f"""
            SELECT snapshot_date, partner_id, locker_id, country_code, jurisdiction_code, currency, timezone,
                   measured_occupied_minutes, measured_occupied_hours::text,
                   billed_storage_units::text, billed_storage_hours::text, billed_storage_amount_cents,
                   difference_hours::text, difference_pct::text, divergence_status, dedupe_key, updated_at
            FROM locker_utilization_snapshots
            WHERE {' AND '.join(clauses)}
            ORDER BY {sort_field} {sort_direction}, updated_at DESC
            LIMIT :limit OFFSET :offset
            """
        ),
        params,
    ).mappings().all()
    count_row = db.execute(
        text(f"SELECT COUNT(*) FROM locker_utilization_snapshots WHERE {' AND '.join(clauses)}"),
        {k: v for k, v in params.items() if k not in ("limit", "offset")},
    ).fetchone()
    items = [_row_to_dict(r) for r in rows]
    return {
        "count": len(items),
        "total": int(count_row[0] if count_row else 0),
        "limit": limit,
        "offset": offset,
        "sort_by": sort_by,
        "sort_order": sort_direction,
        "items": items,
    }


@router.post("/ops/utilization-snapshots/recompute")
def recompute_utilization_snapshots(
    snapshot_date: str = Query(...),
    partner_id: str | None = Query(default=None),
    locker_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _: None = Depends(validate_internal_token),
):
    try:
        parsed_date = datetime.strptime(snapshot_date, "%Y-%m-%d").date()
    except ValueError as exc:
        raise _api_error(422, "INVALID_SNAPSHOT_DATE", "snapshot_date must be YYYY-MM-DD", {"snapshot_date": snapshot_date}) from exc

    result = recompute_daily_utilization_snapshot(
        db,
        snapshot_date=parsed_date,
        partner_id=partner_id,
        locker_id=locker_id,
    )
    return {"ok": True, **result}
