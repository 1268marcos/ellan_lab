from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy import String, and_, asc, cast, column, desc, func, literal, select, table, text
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
from app.services.accounting_posting_service import PostingEvent, post_event

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


def _resolve_order_expr(sort_field: str, sort_direction: str):
    return asc(column(sort_field)) if sort_direction == "ASC" else desc(column(sort_field))


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
    billing_cycles = table("partner_billing_cycles")
    filters = [column("partner_id") == partner_id]
    if year is not None:
        filters.append(func.extract("year", column("period_start")) == int(year))
    status_norm = _normalize_enum(
        status,
        VALID_CYCLE_STATUS,
        param_name="status",
        error_code="INVALID_CYCLE_STATUS",
    )
    if status_norm:
        filters.append(column("status") == status_norm)
    if country_code:
        filters.append(column("country_code") == country_code.strip().upper())
    if jurisdiction_code:
        filters.append(column("jurisdiction_code") == jurisdiction_code.strip().upper())
    if from_date:
        filters.append(column("period_start") >= from_date)
    if to_date:
        filters.append(column("period_end") <= to_date)
    sort_field, sort_direction = _resolve_sorting(
        sort_by=sort_by,
        sort_order=sort_order,
        allowed_fields=CYCLE_SORT_FIELDS,
        default_field="period_start",
    )

    rows = db.execute(
        select(
            column("id"),
            column("partner_id"),
            column("status"),
            column("currency"),
            column("country_code"),
            column("jurisdiction_code"),
            column("period_timezone"),
            column("period_start"),
            column("period_end"),
            column("total_amount_cents"),
            column("dedupe_key"),
            column("computed_at"),
        )
        .select_from(billing_cycles)
        .where(and_(*filters))
        .order_by(_resolve_order_expr(sort_field, sort_direction), desc(column("created_at")))
        .limit(int(limit))
        .offset(int(offset))
    ).mappings().all()
    count_row = db.execute(
        select(func.count())
        .select_from(billing_cycles)
        .where(and_(*filters))
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
    line_items = table("partner_billing_line_items")
    filters = [column("partner_id") == partner_id, column("cycle_id") == cycle_id]
    line_type_norm = _normalize_enum(
        line_type,
        VALID_LINE_TYPES,
        param_name="line_type",
        error_code="INVALID_LINE_TYPE",
    )
    if line_type_norm:
        filters.append(column("line_type") == line_type_norm)
    if country_code:
        filters.append(column("country_code") == country_code.strip().upper())
    if jurisdiction_code:
        filters.append(column("jurisdiction_code") == jurisdiction_code.strip().upper())
    sort_field, sort_direction = _resolve_sorting(
        sort_by=sort_by,
        sort_order=sort_order,
        allowed_fields=LINE_ITEM_SORT_FIELDS,
        default_field="id",
    )

    rows = db.execute(
        select(
            column("id"),
            column("cycle_id"),
            column("partner_id"),
            column("line_type"),
            column("description"),
            cast(column("quantity"), String).label("quantity"),
            column("unit_price_cents"),
            column("total_cents"),
            column("currency"),
            column("country_code"),
            column("jurisdiction_code"),
            column("dedupe_key"),
            column("created_at"),
        )
        .select_from(line_items)
        .where(and_(*filters))
        .order_by(_resolve_order_expr(sort_field, sort_direction), asc(column("id")))
        .limit(int(limit))
        .offset(int(offset))
    ).mappings().all()
    count_row = db.execute(
        select(func.count())
        .select_from(line_items)
        .where(and_(*filters))
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
    invoices = table("partner_b2b_invoices")
    filters = [column("partner_id") == partner_id]
    status_norm = _normalize_enum(
        status,
        VALID_INVOICE_STATUS,
        param_name="status",
        error_code="INVALID_INVOICE_STATUS",
    )
    if status_norm:
        filters.append(column("status") == status_norm)
    if from_date:
        filters.append(func.date(column("created_at")) >= from_date)
    if to_date:
        filters.append(func.date(column("created_at")) <= to_date)
    if country_code:
        filters.append(column("country_code") == country_code.strip().upper())
    if jurisdiction_code:
        filters.append(column("jurisdiction_code") == jurisdiction_code.strip().upper())
    document_type_norm = _normalize_enum(
        document_type,
        VALID_INVOICE_DOCUMENT_TYPES,
        param_name="document_type",
        error_code="INVALID_DOCUMENT_TYPE",
    )
    if document_type_norm:
        filters.append(column("document_type") == document_type_norm)
    sort_field, sort_direction = _resolve_sorting(
        sort_by=sort_by,
        sort_order=sort_order,
        allowed_fields=INVOICE_SORT_FIELDS,
        default_field="created_at",
    )

    rows = db.execute(
        select(
            column("id"),
            column("cycle_id"),
            column("partner_id"),
            column("status"),
            column("document_type"),
            column("amount_cents"),
            column("tax_cents"),
            column("currency"),
            column("country_code"),
            column("jurisdiction_code"),
            column("timezone"),
            column("due_date"),
            column("dedupe_key"),
            column("created_at"),
        )
        .select_from(invoices)
        .where(and_(*filters))
        .order_by(_resolve_order_expr(sort_field, sort_direction), desc(column("created_at")))
        .limit(int(limit))
        .offset(int(offset))
    ).mappings().all()
    count_row = db.execute(
        select(func.count())
        .select_from(invoices)
        .where(and_(*filters))
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
    credit_notes = table("partner_credit_notes")
    filters = [column("partner_id") == partner_id]
    status_norm = _normalize_enum(
        status,
        VALID_CREDIT_NOTE_STATUS,
        param_name="status",
        error_code="INVALID_CREDIT_NOTE_STATUS",
    )
    if status_norm:
        filters.append(column("status") == status_norm)
    reason_code_norm = _normalize_enum(
        reason_code,
        VALID_CREDIT_NOTE_REASON_CODES,
        param_name="reason_code",
        error_code="INVALID_CREDIT_NOTE_REASON_CODE",
    )
    if reason_code_norm:
        filters.append(column("reason_code") == reason_code_norm)
    if country_code:
        filters.append(column("country_code") == country_code.strip().upper())
    if jurisdiction_code:
        filters.append(column("jurisdiction_code") == jurisdiction_code.strip().upper())
    sort_field, sort_direction = _resolve_sorting(
        sort_by=sort_by,
        sort_order=sort_order,
        allowed_fields=CREDIT_NOTE_SORT_FIELDS,
        default_field="created_at",
    )

    rows = db.execute(
        select(
            column("id"),
            column("partner_id"),
            column("original_invoice_id"),
            column("cycle_id"),
            column("reason_code"),
            column("amount_cents"),
            column("currency"),
            column("country_code"),
            column("jurisdiction_code"),
            column("timezone"),
            column("status"),
            column("dispute_ref"),
            column("dedupe_key"),
            column("created_at"),
        )
        .select_from(credit_notes)
        .where(and_(*filters))
        .order_by(_resolve_order_expr(sort_field, sort_direction), desc(column("created_at")))
        .limit(int(limit))
        .offset(int(offset))
    ).mappings().all()
    count_row = db.execute(
        select(func.count())
        .select_from(credit_notes)
        .where(and_(*filters))
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
    cycles = table("partner_billing_cycles")
    filters = [column("partner_id") == partner_id, column("status") == "DISPUTED"]
    if status:
        status_norm = _normalize_enum(
            status,
            VALID_CYCLE_STATUS,
            param_name="status",
            error_code="INVALID_CYCLE_STATUS",
        )
        filters.append(column("status") == status_norm)
    if from_date:
        filters.append(func.date(column("updated_at")) >= from_date)
    if to_date:
        filters.append(func.date(column("updated_at")) <= to_date)
    if country_code:
        filters.append(column("country_code") == country_code.strip().upper())
    if jurisdiction_code:
        filters.append(column("jurisdiction_code") == jurisdiction_code.strip().upper())
    sort_field, sort_direction = _resolve_sorting(
        sort_by=sort_by,
        sort_order=sort_order,
        allowed_fields=DISPUTE_SORT_FIELDS,
        default_field="opened_at",
    )

    rows = db.execute(
        select(
            column("id").label("cycle_id"),
            column("partner_id"),
            literal("CYCLE").label("dispute_scope"),
            column("dispute_reason"),
            column("status"),
            column("country_code"),
            column("jurisdiction_code"),
            func.coalesce(column("updated_at"), column("created_at")).label("opened_at"),
            func.jsonb_build_object("dedupe_key", column("dedupe_key")).label("metadata"),
        )
        .select_from(cycles)
        .where(and_(*filters))
        .order_by(_resolve_order_expr(sort_field, sort_direction), desc(func.coalesce(column("updated_at"), column("created_at"))))
        .limit(int(limit))
        .offset(int(offset))
    ).mappings().all()
    count_row = db.execute(
        select(func.count())
        .select_from(cycles)
        .where(and_(*filters))
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
    utilization = table("locker_utilization_snapshots")
    filters = []
    if snapshot_date:
        filters.append(column("snapshot_date") == snapshot_date)
    if from_date:
        filters.append(column("snapshot_date") >= from_date)
    if to_date:
        filters.append(column("snapshot_date") <= to_date)
    if partner_id:
        filters.append(column("partner_id") == partner_id)
    if locker_id:
        filters.append(column("locker_id") == locker_id)
    if country_code:
        filters.append(column("country_code") == country_code.strip().upper())
    if jurisdiction_code:
        filters.append(column("jurisdiction_code") == jurisdiction_code.strip().upper())
    status_norm = _normalize_enum(
        divergence_status,
        VALID_UTILIZATION_STATUS,
        param_name="divergence_status",
        error_code="INVALID_UTILIZATION_STATUS",
    )
    if status_norm:
        filters.append(column("divergence_status") == status_norm)
    sort_field, sort_direction = _resolve_sorting(
        sort_by=sort_by,
        sort_order=sort_order,
        allowed_fields=UTILIZATION_SORT_FIELDS,
        default_field="snapshot_date",
    )

    rows = db.execute(
        select(
            column("snapshot_date"),
            column("partner_id"),
            column("locker_id"),
            column("country_code"),
            column("jurisdiction_code"),
            column("currency"),
            column("timezone"),
            column("measured_occupied_minutes"),
            cast(column("measured_occupied_hours"), String).label("measured_occupied_hours"),
            cast(column("billed_storage_units"), String).label("billed_storage_units"),
            cast(column("billed_storage_hours"), String).label("billed_storage_hours"),
            column("billed_storage_amount_cents"),
            cast(column("difference_hours"), String).label("difference_hours"),
            cast(column("difference_pct"), String).label("difference_pct"),
            column("divergence_status"),
            column("dedupe_key"),
            column("updated_at"),
        )
        .select_from(utilization)
        .where(and_(*filters) if filters else text("1=1"))
        .order_by(_resolve_order_expr(sort_field, sort_direction), desc(column("updated_at")))
        .limit(int(limit))
        .offset(int(offset))
    ).mappings().all()
    count_row = db.execute(
        select(func.count())
        .select_from(utilization)
        .where(and_(*filters) if filters else text("1=1"))
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


@router.post("/{partner_id}/invoices/{invoice_id}/cancel")
def cancel_partner_invoice(
    partner_id: str,
    invoice_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(validate_internal_token),
):
    row = db.execute(
        text(
            """
            UPDATE partner_b2b_invoices
            SET status = 'CANCELLED',
                cancelled_at = NOW(),
                updated_at = NOW()
            WHERE id = :invoice_id
              AND partner_id = :partner_id
              AND status <> 'CANCELLED'
            RETURNING id, amount_cents, currency
            """
        ),
        {"invoice_id": invoice_id, "partner_id": partner_id},
    ).mappings().first()
    if not row:
        raise _api_error(
            404,
            "INVOICE_NOT_FOUND_OR_ALREADY_CANCELLED",
            "Invoice not found or already cancelled",
            {"invoice_id": invoice_id, "partner_id": partner_id},
        )
    db.commit()
    post_result = post_event(
        db,
        PostingEvent(
            event_type="PARTNER_INVOICE_CANCELLED",
            reference_source="partner_b2b_invoice",
            reference_id=invoice_id,
            amount=(Decimal(row.get("amount_cents") or 0) / Decimal("100")),
            currency=row.get("currency") or "BRL",
            description=f"Partner invoice cancelled: {invoice_id}",
        ),
    )
    return {"ok": True, "invoice_id": invoice_id, "status": "CANCELLED", "accounting": post_result}


@router.post("/{partner_id}/credit-notes/{credit_note_id}/apply")
def apply_partner_credit_note(
    partner_id: str,
    credit_note_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(validate_internal_token),
):
    row = db.execute(
        text(
            """
            UPDATE partner_credit_notes
            SET status = 'APPLIED',
                applied_at = NOW(),
                updated_at = NOW()
            WHERE id = :credit_note_id
              AND partner_id = :partner_id
              AND status IN ('PENDING', 'APPROVED')
            RETURNING id, amount_cents, currency
            """
        ),
        {"credit_note_id": credit_note_id, "partner_id": partner_id},
    ).mappings().first()
    if not row:
        raise _api_error(
            404,
            "CREDIT_NOTE_NOT_FOUND_OR_NOT_APPLICABLE",
            "Credit note not found or not in applicable status",
            {"credit_note_id": credit_note_id, "partner_id": partner_id},
        )
    db.commit()
    post_result = post_event(
        db,
        PostingEvent(
            event_type="PARTNER_CREDIT_NOTE_APPLIED",
            reference_source="partner_credit_note",
            reference_id=credit_note_id,
            amount=(Decimal(row.get("amount_cents") or 0) / Decimal("100")),
            currency=row.get("currency") or "BRL",
            description=f"Partner credit note applied: {credit_note_id}",
        ),
    )
    return {"ok": True, "credit_note_id": credit_note_id, "status": "APPLIED", "accounting": post_result}
