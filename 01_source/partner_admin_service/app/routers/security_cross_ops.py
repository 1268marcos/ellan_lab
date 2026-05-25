from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.security_cross_ops import (
    AccessRequestCreateIn,
    AccessRequestDecideIn,
    AccessRequestListOut,
    AccessRequestOut,
    DelegationListOut,
    DelegationOpenIn,
    DelegationOut,
    DomainAccessReportOut,
    DomainEntitlementListOut,
    JitGrantCreateIn,
    JitGrantListOut,
    JitGrantOut,
)
from app.services import security_cross_ops_service

router = APIRouter(prefix="/security-admin/cross-ops", tags=["security-cross-ops"])


@router.get("/access-requests", response_model=AccessRequestListOut)
def list_access_requests(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> AccessRequestListOut:
    return security_cross_ops_service.list_access_requests(db, status)


@router.post("/access-requests", response_model=AccessRequestOut, status_code=status.HTTP_201_CREATED)
def create_access_request(body: AccessRequestCreateIn, db: Session = Depends(get_db)) -> AccessRequestOut:
    return security_cross_ops_service.create_access_request(db, body)


@router.post("/access-requests/{request_id}/decide", response_model=AccessRequestOut)
def decide_access_request(
    request_id: str, body: AccessRequestDecideIn, db: Session = Depends(get_db)
) -> AccessRequestOut:
    return security_cross_ops_service.decide_access_request(db, request_id, body)


@router.get("/jit-grants", response_model=JitGrantListOut)
def list_jit_grants(active_only: bool = Query(True), db: Session = Depends(get_db)) -> JitGrantListOut:
    return security_cross_ops_service.list_jit_grants(db, active_only)


@router.post("/jit-grants", response_model=JitGrantOut, status_code=status.HTTP_201_CREATED)
def create_jit_grant(body: JitGrantCreateIn, db: Session = Depends(get_db)) -> JitGrantOut:
    return security_cross_ops_service.create_jit_grant(db, body)


@router.post("/jit-grants/expire-stale")
def expire_jit(db: Session = Depends(get_db)) -> dict:
    return {"expired": security_cross_ops_service.expire_stale_jit_grants(db)}


@router.get("/delegations", response_model=DelegationListOut)
def list_delegations(active_only: bool = Query(True), db: Session = Depends(get_db)) -> DelegationListOut:
    return security_cross_ops_service.list_delegations(db, active_only)


@router.post("/delegations", response_model=DelegationOut, status_code=status.HTTP_201_CREATED)
def open_delegation(body: DelegationOpenIn, db: Session = Depends(get_db)) -> DelegationOut:
    return security_cross_ops_service.open_delegation(db, body)


@router.post("/delegations/{session_id}/close", response_model=DelegationOut)
def close_delegation(
    session_id: str,
    actor_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> DelegationOut:
    return security_cross_ops_service.close_delegation(db, session_id, actor_id=actor_id)


@router.get("/entitlements", response_model=DomainEntitlementListOut)
def list_entitlements(
    domain_code: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> DomainEntitlementListOut:
    return security_cross_ops_service.list_entitlements(db, domain_code)


@router.post("/entitlements/sync", response_model=DomainEntitlementListOut)
def sync_entitlements(db: Session = Depends(get_db)) -> DomainEntitlementListOut:
    return security_cross_ops_service.sync_domain_entitlements(db)


@router.get("/users/{user_id}/domain-access-report", response_model=DomainAccessReportOut)
def domain_access_report(user_id: str, db: Session = Depends(get_db)) -> DomainAccessReportOut:
    return security_cross_ops_service.domain_access_report(db, user_id)


@router.post("/seed")
def seed_cross_ops(db: Session = Depends(get_db)) -> dict:
    return security_cross_ops_service.seed_cross_ops(db)
