from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.partner import EcommercePartner, LogisticsPartner
from app.schemas.partner import (
    EcommercePartnerCreateIn,
    EcommercePartnerOut,
    EcommercePartnerUpdateIn,
    LogisticsPartnerCreateIn,
    LogisticsPartnerOut,
    LogisticsPartnerUpdateIn,
)
from app.services.crypto_util import new_id


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def list_ecommerce(db: Session, *, active_only: bool = False) -> list[EcommercePartnerOut]:
    q = db.query(EcommercePartner)
    if active_only:
        q = q.filter(EcommercePartner.active.is_(True))
    rows = q.order_by(EcommercePartner.name).all()
    return [EcommercePartnerOut.model_validate(r) for r in rows]


def get_ecommerce_or_404(db: Session, partner_id: str) -> EcommercePartner:
    row = db.get(EcommercePartner, partner_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ecommerce_partner_not_found")
    return row


def create_ecommerce(db: Session, body: EcommercePartnerCreateIn) -> EcommercePartnerOut:
    pid = body.id or new_id()
    if db.get(EcommercePartner, pid):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="partner_id_exists")
    if db.query(EcommercePartner).filter(EcommercePartner.code == body.code).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="partner_code_exists")
    now = _utcnow()
    row = EcommercePartner(
        id=pid,
        name=body.name,
        code=body.code,
        integration_type=body.integration_type,
        api_base_url=body.api_base_url,
        revenue_share_pct=body.revenue_share_pct,
        sla_pickup_hours=body.sla_pickup_hours,
        active=body.active,
        country=body.country,
        status=body.status,
        legal_name=body.legal_name,
        tax_id=body.tax_id,
        tier=body.tier,
        support_email=body.support_email,
        support_phone=body.support_phone,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return EcommercePartnerOut.model_validate(row)


def update_ecommerce(db: Session, partner_id: str, body: EcommercePartnerUpdateIn) -> EcommercePartnerOut:
    row = get_ecommerce_or_404(db, partner_id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    row.updated_at = _utcnow()
    db.commit()
    db.refresh(row)
    return EcommercePartnerOut.model_validate(row)


def delete_ecommerce(db: Session, partner_id: str) -> None:
    row = get_ecommerce_or_404(db, partner_id)
    db.delete(row)
    db.commit()


def list_logistics(db: Session, *, active_only: bool = False) -> list[LogisticsPartnerOut]:
    q = db.query(LogisticsPartner)
    if active_only:
        q = q.filter(LogisticsPartner.active.is_(True))
    rows = q.order_by(LogisticsPartner.name).all()
    return [LogisticsPartnerOut.model_validate(r) for r in rows]


def get_logistics_or_404(db: Session, partner_id: str) -> LogisticsPartner:
    row = db.get(LogisticsPartner, partner_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="logistics_partner_not_found")
    return row


def create_logistics(db: Session, body: LogisticsPartnerCreateIn) -> LogisticsPartnerOut:
    pid = body.id or new_id()
    if db.get(LogisticsPartner, pid):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="partner_id_exists")
    if db.query(LogisticsPartner).filter(LogisticsPartner.code == body.code).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="partner_code_exists")
    now = _utcnow()
    row = LogisticsPartner(
        id=pid,
        name=body.name,
        code=body.code,
        integration_type=body.integration_type,
        api_base_url=body.api_base_url,
        tracking_url_template=body.tracking_url_template,
        auth_type=body.auth_type,
        default_sla_hours=body.default_sla_hours,
        reminder_hours_before=body.reminder_hours_before,
        active=body.active,
        country=body.country,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return LogisticsPartnerOut.model_validate(row)


def update_logistics(db: Session, partner_id: str, body: LogisticsPartnerUpdateIn) -> LogisticsPartnerOut:
    row = get_logistics_or_404(db, partner_id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    row.updated_at = _utcnow()
    db.commit()
    db.refresh(row)
    return LogisticsPartnerOut.model_validate(row)


def delete_logistics(db: Session, partner_id: str) -> None:
    row = get_logistics_or_404(db, partner_id)
    db.delete(row)
    db.commit()
