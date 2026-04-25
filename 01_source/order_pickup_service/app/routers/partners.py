from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.auth_dep import get_current_user, require_user_roles
from app.core.db import get_db
from app.models.partner_contact import PartnerContact
from app.models.partner_sla_agreement import PartnerSlaAgreement
from app.models.partner_status_history import PartnerStatusHistory
from app.models.user import User
from app.services.ops_audit_service import record_ops_action_audit
from app.schemas.partners import (
    PartnerContactPatchIn,
    PartnerContactIn,
    PartnerContactListOut,
    PartnerContactOut,
    PartnerDeleteOut,
    PartnerSlaAgreementPatchIn,
    PartnerSlaAgreementIn,
    PartnerSlaAgreementListOut,
    PartnerSlaAgreementOut,
    PartnerStatusHistoryItemOut,
    PartnerStatusHistoryListOut,
    PartnerStatusOut,
    PartnerStatusTransitionIn,
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
