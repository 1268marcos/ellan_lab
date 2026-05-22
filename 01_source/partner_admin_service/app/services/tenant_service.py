from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.tenant import CustomDomain, TenantFiscalConfig, TenantPartnerLink
from app.schemas.tenant import (
    CustomDomainCreateIn,
    TenantCreateIn,
    TenantPartnerLinkCreateIn,
    TenantUpdateIn,
)
from app.services.crypto_util import new_id


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def list_tenants(db: Session, active_only: bool = False) -> list[TenantFiscalConfig]:
    q = db.query(TenantFiscalConfig)
    if active_only:
        q = q.filter(TenantFiscalConfig.is_active.is_(True))
    return q.order_by(TenantFiscalConfig.tenant_id).all()


def get_tenant_or_404(db: Session, tenant_id: str) -> TenantFiscalConfig:
    row = db.get(TenantFiscalConfig, tenant_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="tenant_not_found")
    return row


def create_tenant(db: Session, body: TenantCreateIn) -> TenantFiscalConfig:
    if db.get(TenantFiscalConfig, body.tenant_id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="tenant_id_exists")
    row = TenantFiscalConfig(**body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_tenant(db: Session, tenant_id: str, body: TenantUpdateIn) -> TenantFiscalConfig:
    row = get_tenant_or_404(db, tenant_id)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    db.commit()
    db.refresh(row)
    return row


def delete_tenant(db: Session, tenant_id: str) -> None:
    row = get_tenant_or_404(db, tenant_id)
    db.query(CustomDomain).filter(CustomDomain.tenant_id == tenant_id).delete()
    db.query(TenantPartnerLink).filter(TenantPartnerLink.tenant_id == tenant_id).delete()
    db.delete(row)
    db.commit()


def list_domains(db: Session, tenant_id: str) -> list[CustomDomain]:
    get_tenant_or_404(db, tenant_id)
    return (
        db.query(CustomDomain)
        .filter(CustomDomain.tenant_id == tenant_id)
        .order_by(CustomDomain.domain)
        .all()
    )


def add_domain(db: Session, tenant_id: str, body: CustomDomainCreateIn) -> CustomDomain:
    get_tenant_or_404(db, tenant_id)
    if db.query(CustomDomain).filter(CustomDomain.domain == body.domain).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="domain_exists")
    now = _utcnow()
    row = CustomDomain(
        id=body.id or new_id(),
        tenant_id=tenant_id,
        domain=body.domain,
        verified=body.verified,
        ssl_cert_ref=body.ssl_cert_ref,
        created_at=now,
        verified_at=now if body.verified else None,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def delete_domain(db: Session, tenant_id: str, domain_id: str) -> None:
    get_tenant_or_404(db, tenant_id)
    row = db.get(CustomDomain, domain_id)
    if not row or row.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="domain_not_found")
    db.delete(row)
    db.commit()


def list_partner_links(db: Session, tenant_id: str) -> list[TenantPartnerLink]:
    get_tenant_or_404(db, tenant_id)
    return (
        db.query(TenantPartnerLink)
        .filter(TenantPartnerLink.tenant_id == tenant_id)
        .order_by(TenantPartnerLink.created_at.desc())
        .all()
    )


def add_partner_link(db: Session, tenant_id: str, body: TenantPartnerLinkCreateIn) -> TenantPartnerLink:
    get_tenant_or_404(db, tenant_id)
    pt = body.partner_type.upper()
    if body.is_default:
        db.query(TenantPartnerLink).filter(
            TenantPartnerLink.tenant_id == tenant_id,
            TenantPartnerLink.partner_type == pt,
            TenantPartnerLink.is_default.is_(True),
        ).update({"is_default": False})
    row = TenantPartnerLink(
        id=body.id or new_id(),
        tenant_id=tenant_id,
        partner_id=body.partner_id,
        partner_type=pt,
        is_default=body.is_default,
        created_at=_utcnow(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def delete_partner_link(db: Session, tenant_id: str, link_id: str) -> None:
    get_tenant_or_404(db, tenant_id)
    row = db.get(TenantPartnerLink, link_id)
    if not row or row.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="link_not_found")
    db.delete(row)
    db.commit()
