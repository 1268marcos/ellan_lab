from __future__ import annotations

import json
from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.clients.domain_http import DomainHttpError, fetch_items
from app.core.config import get_settings
from app.models.security import (
    SecurityAccessRequest,
    SecurityCrossDomainGrant,
    SecurityDelegationSession,
    SecurityDomainEntitlement,
    SecurityJitGrant,
    SecurityUserPlayerAccess,
    UserDomainLink,
)
from app.models.user import User, UserRole
from app.schemas.security import CrossDomainGrantCreateIn
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
    DomainEntitlementOut,
    JitGrantCreateIn,
    JitGrantListOut,
    JitGrantOut,
)
from app.services import user_role_service
from app.services.crypto_util import new_id
from app.services.security_professional_service import create_cross_domain_grant
from app.services.security_service import _parse_json, _utcnow, write_audit
from app.services.security_value_service import _revoke_cross_domain_grant


def _now():
    return _utcnow()


def create_access_request(db: Session, body: AccessRequestCreateIn) -> AccessRequestOut:
    user_role_service.get_user_or_404(db, body.user_id)
    row = SecurityAccessRequest(
        id=new_id(),
        requester_id=body.requester_id,
        user_id=body.user_id,
        domain_code=body.domain_code.upper(),
        entity_type=body.entity_type,
        entity_id=body.entity_id,
        entity_label=body.entity_label,
        permission_key=body.permission_key,
        justification=body.justification,
        status="PENDING",
        created_at=_now(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    write_audit(
        db,
        actor_id=body.requester_id,
        action="ACCESS_REQUEST_CREATED",
        target_type="AccessRequest",
        target_id=row.id,
        new_state={"domain": row.domain_code, "user_id": row.user_id},
    )
    return AccessRequestOut.model_validate(row)


def list_access_requests(db: Session, status_filter: str | None = None) -> AccessRequestListOut:
    q = db.query(SecurityAccessRequest)
    if status_filter:
        q = q.filter(SecurityAccessRequest.status == status_filter.upper())
    rows = q.order_by(SecurityAccessRequest.created_at.desc()).limit(100).all()
    pending = db.query(SecurityAccessRequest).filter(SecurityAccessRequest.status == "PENDING").count()
    return AccessRequestListOut(
        items=[AccessRequestOut.model_validate(r) for r in rows],
        total=len(rows),
        pending_count=pending,
    )


def decide_access_request(db: Session, request_id: str, body: AccessRequestDecideIn) -> AccessRequestOut:
    row = db.get(SecurityAccessRequest, request_id)
    if not row:
        raise HTTPException(status_code=404, detail="access_request_not_found")
    if row.status != "PENDING":
        raise HTTPException(status_code=409, detail="access_request_not_pending")
    row.reviewer_id = body.reviewer_id
    row.reviewed_at = _now()
    row.review_notes = body.review_notes
    if body.decision == "DENY":
        row.status = "DENIED"
    else:
        grant = create_cross_domain_grant(
            db,
            CrossDomainGrantCreateIn(
                user_id=row.user_id,
                domain_code=row.domain_code,
                entity_type=row.entity_type,
                entity_id=row.entity_id,
                entity_label=row.entity_label,
                permission_key=row.permission_key,
            ),
            granted_by=body.reviewer_id,
        )
        row.grant_id = grant.id
        row.status = "APPROVED"
    db.commit()
    db.refresh(row)
    write_audit(
        db,
        actor_id=body.reviewer_id,
        action="ACCESS_REQUEST_DECIDED",
        target_type="AccessRequest",
        target_id=row.id,
        new_state={"decision": body.decision, "grant_id": row.grant_id},
    )
    return AccessRequestOut.model_validate(row)


def expire_stale_jit_grants(db: Session) -> int:
    now = _now()
    n = 0
    rows = (
        db.query(SecurityJitGrant)
        .filter(SecurityJitGrant.status == "ACTIVE", SecurityJitGrant.expires_at <= now)
        .all()
    )
    for j in rows:
        if j.grant_id:
            _revoke_cross_domain_grant(db, j.grant_id, actor_id="system")
        j.status = "EXPIRED"
        j.revoked_at = now
        n += 1
    if n:
        db.commit()
    return n


def create_jit_grant(db: Session, body: JitGrantCreateIn) -> JitGrantOut:
    user_role_service.get_user_or_404(db, body.user_id)
    expire_stale_jit_grants(db)
    now = _now()
    grant = create_cross_domain_grant(
        db,
        CrossDomainGrantCreateIn(
            user_id=body.user_id,
            domain_code=body.domain_code.upper(),
            entity_type=body.entity_type,
            entity_id=body.entity_id,
            entity_label=body.entity_label,
            permission_key=body.permission_key,
            expires_at=now + timedelta(hours=body.duration_hours),
        ),
        granted_by=body.approved_by,
    )
    row = SecurityJitGrant(
        id=new_id(),
        user_id=body.user_id,
        domain_code=body.domain_code.upper(),
        entity_type=body.entity_type,
        entity_id=body.entity_id,
        permission_key=body.permission_key,
        grant_id=grant.id,
        reason=body.reason,
        approved_by=body.approved_by,
        status="ACTIVE",
        started_at=now,
        expires_at=now + timedelta(hours=body.duration_hours),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    write_audit(
        db,
        actor_id=body.approved_by,
        action="JIT_GRANT_OPENED",
        target_type="User",
        target_id=body.user_id,
        new_state={"grant_id": grant.id, "hours": body.duration_hours},
    )
    return JitGrantOut.model_validate(row)


def list_jit_grants(db: Session, active_only: bool = True) -> JitGrantListOut:
    expire_stale_jit_grants(db)
    q = db.query(SecurityJitGrant)
    if active_only:
        q = q.filter(SecurityJitGrant.status == "ACTIVE")
    rows = q.order_by(SecurityJitGrant.expires_at.asc()).limit(50).all()
    return JitGrantListOut(items=[JitGrantOut.model_validate(r) for r in rows], total=len(rows))


def expire_stale_delegations(db: Session) -> int:
    now = _now()
    n = 0
    for d in (
        db.query(SecurityDelegationSession)
        .filter(SecurityDelegationSession.status == "ACTIVE", SecurityDelegationSession.expires_at <= now)
        .all()
    ):
        d.status = "EXPIRED"
        d.ended_at = now
        n += 1
    if n:
        db.commit()
    return n


def open_delegation(db: Session, body: DelegationOpenIn) -> DelegationOut:
    user_role_service.get_user_or_404(db, body.delegate_user_id)
    expire_stale_delegations(db)
    now = _now()
    row = SecurityDelegationSession(
        id=new_id(),
        delegate_user_id=body.delegate_user_id,
        target_domain=body.target_domain.upper(),
        target_entity_type=body.target_entity_type,
        target_entity_id=body.target_entity_id,
        target_entity_label=body.target_entity_label,
        reason=body.reason,
        approved_by=body.approved_by,
        status="ACTIVE",
        started_at=now,
        expires_at=now + timedelta(hours=body.duration_hours),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    write_audit(
        db,
        actor_id=body.approved_by,
        action="DELEGATION_OPENED",
        target_type="User",
        target_id=body.delegate_user_id,
        new_state={"domain": row.target_domain, "entity_id": row.target_entity_id},
    )
    return DelegationOut.model_validate(row)


def close_delegation(db: Session, session_id: str, *, actor_id: str | None = None) -> DelegationOut:
    row = db.get(SecurityDelegationSession, session_id)
    if not row:
        raise HTTPException(status_code=404, detail="delegation_not_found")
    if row.status != "ACTIVE":
        raise HTTPException(status_code=409, detail="delegation_not_active")
    row.status = "CLOSED"
    row.ended_at = _now()
    db.commit()
    db.refresh(row)
    write_audit(
        db,
        actor_id=actor_id,
        action="DELEGATION_CLOSED",
        target_type="DelegationSession",
        target_id=row.id,
        new_state={},
    )
    return DelegationOut.model_validate(row)


def list_delegations(db: Session, active_only: bool = True) -> DelegationListOut:
    expire_stale_delegations(db)
    q = db.query(SecurityDelegationSession)
    if active_only:
        q = q.filter(SecurityDelegationSession.status == "ACTIVE")
    rows = q.order_by(SecurityDelegationSession.started_at.desc()).limit(50).all()
    return DelegationListOut(items=[DelegationOut.model_validate(r) for r in rows], total=len(rows))


def sync_domain_entitlements(db: Session) -> DomainEntitlementListOut:
    s = get_settings()
    now = _now()
    synced_domains: set[str] = set()
    count = 0

    def upsert(domain: str, etype: str, eid: str, label: str, key: str, source: str, meta: dict) -> None:
        nonlocal count
        existing = (
            db.query(SecurityDomainEntitlement)
            .filter(
                SecurityDomainEntitlement.domain_code == domain,
                SecurityDomainEntitlement.remote_entity_type == etype,
                SecurityDomainEntitlement.remote_entity_id == eid,
                SecurityDomainEntitlement.entitlement_key == key,
            )
            .first()
        )
        if existing:
            existing.remote_label = label
            existing.synced_at = now
            existing.metadata_json = json.dumps(meta)
        else:
            db.add(
                SecurityDomainEntitlement(
                    id=new_id(),
                    domain_code=domain,
                    remote_entity_type=etype,
                    remote_entity_id=eid,
                    remote_label=label,
                    entitlement_key=key,
                    source_service=source,
                    synced_at=now,
                    metadata_json=json.dumps(meta),
                )
            )
            count += 1
        synced_domains.add(domain)

    try:
        for p in fetch_items("PARTNER", f"{s.partner_admin_base_url}/api/v1/partner-admin/ecosystem/players", params={"limit": 40}):
            code = str(p.get("player_code") or p.get("code") or "")
            if code:
                upsert("PARTNER", "EcosystemPlayer", code, str(p.get("name") or code), "ops.partner.read", "partner_admin", p)
    except DomainHttpError:
        pass

    try:
        for c in fetch_items("MARKETPLACE", f"{s.marketplace_admin_url}/api/v1/marketplace-admin/channel-partners"):
            cid = str(c.get("id") or c.get("code") or "")
            if cid:
                upsert("MARKETPLACE", "ChannelPartner", cid, str(c.get("name") or cid), "marketplace.channel.manage", "marketplace_admin", c)
    except DomainHttpError:
        pass

    for g in db.query(SecurityCrossDomainGrant).filter(SecurityCrossDomainGrant.is_active.is_(True)).limit(80).all():
        upsert(g.domain_code, g.entity_type, g.entity_id, g.entity_label or g.entity_id, g.permission_key, "local_grants", {})

    db.commit()
    rows = db.query(SecurityDomainEntitlement).order_by(SecurityDomainEntitlement.synced_at.desc()).limit(200).all()
    return DomainEntitlementListOut(
        items=[DomainEntitlementOut.model_validate(r) for r in rows],
        total=len(rows),
        domains_synced=len(synced_domains),
    )


def list_entitlements(db: Session, domain_code: str | None = None) -> DomainEntitlementListOut:
    q = db.query(SecurityDomainEntitlement)
    if domain_code:
        q = q.filter(SecurityDomainEntitlement.domain_code == domain_code.upper())
    rows = q.order_by(SecurityDomainEntitlement.domain_code, SecurityDomainEntitlement.remote_entity_id).limit(300).all()
    domains = {r.domain_code for r in rows}
    return DomainEntitlementListOut(
        items=[DomainEntitlementOut.model_validate(r) for r in rows],
        total=len(rows),
        domains_synced=len(domains),
    )


def domain_access_report(db: Session, user_id: str) -> DomainAccessReportOut:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user_not_found")
    roles = [
        r.role
        for r in db.query(UserRole)
        .filter(UserRole.user_id == user_id, UserRole.is_active.is_(True), UserRole.revoked_at.is_(None))
        .all()
    ]
    links = [
        {
            "domain": l.domain,
            "entity_type": l.entity_type,
            "entity_id": l.entity_id,
            "relation": l.relation,
        }
        for l in db.query(UserDomainLink).filter(UserDomainLink.user_id == user_id).all()
    ]
    grants = [
        {
            "domain": g.domain_code,
            "entity_id": g.entity_id,
            "permission": g.permission_key,
            "expires_at": g.expires_at.isoformat() if g.expires_at else None,
        }
        for g in db.query(SecurityCrossDomainGrant)
        .filter(SecurityCrossDomainGrant.user_id == user_id, SecurityCrossDomainGrant.is_active.is_(True))
        .all()
    ]
    players = [
        {"player_code": a.player_code, "access_role": a.access_role}
        for a in db.query(SecurityUserPlayerAccess).filter(SecurityUserPlayerAccess.user_id == user_id).all()
    ]
    pending = db.query(SecurityAccessRequest).filter(
        SecurityAccessRequest.user_id == user_id, SecurityAccessRequest.status == "PENDING"
    ).count()
    jit = db.query(SecurityJitGrant).filter(SecurityJitGrant.user_id == user_id, SecurityJitGrant.status == "ACTIVE").count()
    deleg = db.query(SecurityDelegationSession).filter(
        SecurityDelegationSession.delegate_user_id == user_id, SecurityDelegationSession.status == "ACTIVE"
    ).count()
    ent_keys = {g["domain"] for g in grants}
    remote = [
        {
            "domain": e.domain_code,
            "entity_id": e.remote_entity_id,
            "entitlement": e.entitlement_key,
        }
        for e in db.query(SecurityDomainEntitlement).filter(SecurityDomainEntitlement.domain_code.in_(ent_keys or ["PARTNER"])).limit(30).all()
    ]
    return DomainAccessReportOut(
        user_id=user_id,
        roles=roles,
        domain_links=links,
        active_grants=grants,
        pending_requests=pending,
        active_jit=jit,
        active_delegations=deleg,
        player_access=players,
        remote_entitlements=remote,
    )


def seed_cross_ops(db: Session) -> dict[str, int]:
    counts: dict[str, int] = {}
    if not db.query(SecurityAccessRequest).first():
        req = create_access_request(
            db,
            AccessRequestCreateIn(
                requester_id="usr-suporte",
                user_id="usr-suporte",
                domain_code="MARKETPLACE",
                entity_type="ChannelPartner",
                entity_id="MAGALU",
                entity_label="Magalu",
                permission_key="marketplace.sellers.manage",
                justification="Onboarding seller Magalu Q2",
            ),
        )
        decide_access_request(
            db,
            req.id,
            AccessRequestDecideIn(decision="APPROVE", reviewer_id="usr-admin-ops", review_notes="Aprovado OPS"),
        )
        counts["access_requests"] = 1
    if not db.query(SecurityJitGrant).first():
        create_jit_grant(
            db,
            JitGrantCreateIn(
                user_id="usr-auditoria",
                domain_code="PAYMENT_GATEWAY",
                entity_type="PSP",
                entity_id="STRIPE_SANDBOX",
                permission_key="payment.refunds.read",
                reason="Auditoria incidente chargeback",
                duration_hours=6,
                approved_by="usr-admin-ops",
            ),
        )
        counts["jit"] = 1
    if not db.query(SecurityDelegationSession).first():
        open_delegation(
            db,
            DelegationOpenIn(
                delegate_user_id="usr-admin-ops",
                target_domain="PARTNER",
                target_entity_type="LogisticsPartner",
                target_entity_id="INPOST",
                target_entity_label="InPost",
                reason="Suporte incidente rede InPost",
                duration_hours=2,
                approved_by="usr-admin-ops",
            ),
        )
        counts["delegations"] = 1
    sync_domain_entitlements(db)
    counts["entitlements"] = db.query(SecurityDomainEntitlement).count()
    return counts
