from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.tenant import (
    CustomDomainCreateIn,
    CustomDomainListOut,
    CustomDomainOut,
    TenantCreateIn,
    TenantListOut,
    TenantOut,
    TenantPartnerLinkCreateIn,
    TenantPartnerLinkListOut,
    TenantPartnerLinkOut,
    TenantUpdateIn,
)
from app.services import tenant_service

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.get("", response_model=TenantListOut)
def list_tenants(active_only: bool = Query(False), db: Session = Depends(get_db)) -> TenantListOut:
    tenants = tenant_service.list_tenants(db, active_only=active_only)
    out = [TenantOut.model_validate(t) for t in tenants]
    return TenantListOut(tenants=out, total=len(out))


@router.post("", response_model=TenantOut, status_code=status.HTTP_201_CREATED)
def create_tenant(body: TenantCreateIn, db: Session = Depends(get_db)) -> TenantOut:
    return TenantOut.model_validate(tenant_service.create_tenant(db, body))


@router.get("/{tenant_id}", response_model=TenantOut)
def get_tenant(tenant_id: str, db: Session = Depends(get_db)) -> TenantOut:
    return TenantOut.model_validate(tenant_service.get_tenant_or_404(db, tenant_id))


@router.patch("/{tenant_id}", response_model=TenantOut)
def update_tenant(
    tenant_id: str, body: TenantUpdateIn, db: Session = Depends(get_db)
) -> TenantOut:
    return TenantOut.model_validate(tenant_service.update_tenant(db, tenant_id, body))


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tenant(tenant_id: str, db: Session = Depends(get_db)) -> None:
    tenant_service.delete_tenant(db, tenant_id)


@router.get("/{tenant_id}/domains", response_model=CustomDomainListOut)
def list_domains(tenant_id: str, db: Session = Depends(get_db)) -> CustomDomainListOut:
    domains = tenant_service.list_domains(db, tenant_id)
    out = [CustomDomainOut.model_validate(d) for d in domains]
    return CustomDomainListOut(domains=out, total=len(out))


@router.post("/{tenant_id}/domains", response_model=CustomDomainOut, status_code=status.HTTP_201_CREATED)
def add_domain(
    tenant_id: str, body: CustomDomainCreateIn, db: Session = Depends(get_db)
) -> CustomDomainOut:
    return CustomDomainOut.model_validate(tenant_service.add_domain(db, tenant_id, body))


@router.delete("/{tenant_id}/domains/{domain_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_domain(tenant_id: str, domain_id: str, db: Session = Depends(get_db)) -> None:
    tenant_service.delete_domain(db, tenant_id, domain_id)


@router.get("/{tenant_id}/partner-links", response_model=TenantPartnerLinkListOut)
def list_partner_links(tenant_id: str, db: Session = Depends(get_db)) -> TenantPartnerLinkListOut:
    links = tenant_service.list_partner_links(db, tenant_id)
    out = [TenantPartnerLinkOut.model_validate(l) for l in links]
    return TenantPartnerLinkListOut(links=out, total=len(out))


@router.post(
    "/{tenant_id}/partner-links",
    response_model=TenantPartnerLinkOut,
    status_code=status.HTTP_201_CREATED,
)
def add_partner_link(
    tenant_id: str, body: TenantPartnerLinkCreateIn, db: Session = Depends(get_db)
) -> TenantPartnerLinkOut:
    return TenantPartnerLinkOut.model_validate(tenant_service.add_partner_link(db, tenant_id, body))


@router.delete("/{tenant_id}/partner-links/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_partner_link(tenant_id: str, link_id: str, db: Session = Depends(get_db)) -> None:
    tenant_service.delete_partner_link(db, tenant_id, link_id)
