from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.security import (
    SecurityApiKey,
    SecurityAuditLog,
    SecurityCrossDomainGrant,
    SecurityDomainCatalog,
    SecurityIdentityProvider,
    SecurityLockerPlayerRegistry,
    SecurityPermission,
    SecurityUserPlayerAccess,
    SecurityPermissionGroup,
    SecurityPermissionMembership,
    SecurityPolicySnapshot,
    SecurityRoleCatalog,
    SecurityUserSession,
    SecurityWebhookDelivery,
    SecurityWebhookEndpoint,
    UserDomainLink,
)
from app.models.user import User, UserRole
from app.schemas.security import (
    ApiKeyListOut,
    ApiKeyMetaOut,
    ApiKeyRotateIn,
    ApiKeyRotateOut,
    AuditLogListOut,
    AuditLogOut,
    DomainLinkCreateIn,
    DomainLinkListOut,
    DomainLinkOut,
    MembershipCreateIn,
    MembershipListOut,
    MembershipOut,
    PermissionCreateIn,
    PermissionGroupCreateIn,
    PermissionGroupListOut,
    PermissionGroupOut,
    PermissionListOut,
    PermissionOut,
    SecuritySummaryOut,
    WebhookEndpointCreateIn,
    WebhookEndpointListOut,
    WebhookEndpointOut,
    WebhookRotateOut,
)
from app.services.crypto_util import hash_secret, new_id


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse_json(text: str | None, default: Any) -> Any:
    if not text:
        return default
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return default


def write_audit(
    db: Session,
    *,
    actor_id: str | None = None,
    actor_role: str | None = None,
    action: str,
    target_type: str,
    target_id: str,
    old_state: dict | None = None,
    new_state: dict | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> None:
    db.add(
        SecurityAuditLog(
            id=new_id(),
            actor_id=actor_id,
            actor_role=actor_role,
            action=action,
            target_type=target_type,
            target_id=target_id,
            old_state_json=json.dumps(old_state) if old_state else None,
            new_state_json=json.dumps(new_state) if new_state else None,
            ip_address=ip_address,
            user_agent=user_agent,
            occurred_at=_utcnow(),
        )
    )
    db.commit()


def get_summary(db: Session) -> SecuritySummaryOut:
    from app.services.security_professional_service import probe_domain_health

    active_roles = (
        db.query(UserRole)
        .filter(UserRole.is_active.is_(True), UserRole.revoked_at.is_(None))
        .count()
    )
    active_keys = db.query(SecurityApiKey).filter(SecurityApiKey.revoked_at.is_(None)).count()
    health = probe_domain_health(db)
    return SecuritySummaryOut(
        users=db.query(User).count(),
        active_roles=active_roles,
        permission_groups=db.query(SecurityPermissionGroup).count(),
        webhook_endpoints=db.query(SecurityWebhookEndpoint).count(),
        active_api_keys=active_keys,
        audit_logs=db.query(SecurityAuditLog).count(),
        domain_links=db.query(UserDomainLink).count(),
        domain_catalog=db.query(SecurityDomainCatalog).count(),
        role_catalog=db.query(SecurityRoleCatalog).count(),
        cross_domain_grants=db.query(SecurityCrossDomainGrant).filter(SecurityCrossDomainGrant.is_active.is_(True)).count(),
        active_sessions=db.query(SecurityUserSession).filter(SecurityUserSession.revoked_at.is_(None)).count(),
        webhook_deliveries=db.query(SecurityWebhookDelivery).count(),
        identity_providers=db.query(SecurityIdentityProvider).count(),
        policy_snapshots=db.query(SecurityPolicySnapshot).count(),
        domains_reachable=health.reachable_count,
        domains_total=health.total,
        locker_players=db.query(SecurityLockerPlayerRegistry).filter(SecurityLockerPlayerRegistry.is_active.is_(True)).count(),
        user_player_access=db.query(SecurityUserPlayerAccess).filter(SecurityUserPlayerAccess.is_active.is_(True)).count(),
    )


def list_permission_groups(db: Session) -> PermissionGroupListOut:
    rows = db.query(SecurityPermissionGroup).order_by(SecurityPermissionGroup.name).all()
    return PermissionGroupListOut(
        items=[PermissionGroupOut.model_validate(r) for r in rows],
        total=len(rows),
    )


def create_permission_group(db: Session, body: PermissionGroupCreateIn) -> PermissionGroupOut:
    if db.query(SecurityPermissionGroup).filter(SecurityPermissionGroup.name == body.name).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="group_name_exists")
    now = _utcnow()
    row = SecurityPermissionGroup(
        id=new_id(),
        name=body.name,
        description=body.description,
        is_system=False,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    write_audit(db, action="PERMISSION_GROUP_CREATED", target_type="PermissionGroup", target_id=row.id, new_state={"name": row.name})
    return PermissionGroupOut.model_validate(row)


def list_permissions(db: Session, group_id: str | None = None) -> PermissionListOut:
    q = db.query(SecurityPermission)
    if group_id:
        q = q.filter(SecurityPermission.group_id == group_id)
    rows = q.order_by(SecurityPermission.object_key).all()
    return PermissionListOut(items=[PermissionOut.model_validate(r) for r in rows], total=len(rows))


def create_permission(db: Session, body: PermissionCreateIn) -> PermissionOut:
    if not db.get(SecurityPermissionGroup, body.group_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="group_not_found")
    row = SecurityPermission(id=new_id(), group_id=body.group_id, object_key=body.object_key, created_at=_utcnow())
    db.add(row)
    db.commit()
    db.refresh(row)
    return PermissionOut.model_validate(row)


def list_memberships(db: Session, user_id: str | None = None) -> MembershipListOut:
    q = db.query(SecurityPermissionMembership)
    if user_id:
        q = q.filter(SecurityPermissionMembership.user_id == user_id)
    rows = q.all()
    return MembershipListOut(items=[MembershipOut.model_validate(r) for r in rows], total=len(rows))


def create_membership(db: Session, body: MembershipCreateIn) -> MembershipOut:
    if not db.get(User, body.user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user_not_found")
    if not db.get(SecurityPermissionGroup, body.group_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="group_not_found")
    row = SecurityPermissionMembership(
        id=new_id(),
        user_id=body.user_id,
        group_id=body.group_id,
        is_group_manager=body.is_group_manager,
        created_at=_utcnow(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return MembershipOut.model_validate(row)


def _webhook_out(row: SecurityWebhookEndpoint) -> WebhookEndpointOut:
    return WebhookEndpointOut(
        id=row.id,
        owner_type=row.owner_type,
        owner_id=row.owner_id,
        url=row.url,
        events=_parse_json(row.events_json, ["*"]),
        secret_prefix=row.secret_prefix,
        signing_algo=row.signing_algo,
        active=row.active,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def list_webhooks(db: Session) -> WebhookEndpointListOut:
    rows = db.query(SecurityWebhookEndpoint).order_by(SecurityWebhookEndpoint.created_at.desc()).all()
    return WebhookEndpointListOut(items=[_webhook_out(r) for r in rows], total=len(rows))


def create_webhook(db: Session, body: WebhookEndpointCreateIn) -> tuple[WebhookEndpointOut, str]:
    secret = secrets.token_urlsafe(32)
    prefix = secret[:8]
    now = _utcnow()
    row = SecurityWebhookEndpoint(
        id=new_id(),
        owner_type=body.owner_type,
        owner_id=body.owner_id,
        url=body.url,
        events_json=json.dumps(body.events),
        secret_hash=hash_secret(secret),
        secret_prefix=prefix,
        signing_algo=body.signing_algo,
        active=body.active,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    write_audit(db, action="WEBHOOK_CREATED", target_type="WebhookEndpoint", target_id=row.id, new_state={"url": row.url})
    return _webhook_out(row), secret


def rotate_webhook_secret(db: Session, endpoint_id: str) -> WebhookRotateOut:
    row = db.get(SecurityWebhookEndpoint, endpoint_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="webhook_not_found")
    secret = secrets.token_urlsafe(32)
    row.secret_hash = hash_secret(secret)
    row.secret_prefix = secret[:8]
    row.updated_at = _utcnow()
    db.commit()
    write_audit(db, action="WEBHOOK_SECRET_ROTATED", target_type="WebhookEndpoint", target_id=row.id)
    return WebhookRotateOut(endpoint_id=row.id, secret_prefix=row.secret_prefix or "", webhook_secret=secret)


def _api_key_meta(row: SecurityApiKey) -> ApiKeyMetaOut:
    return ApiKeyMetaOut(
        id=row.id,
        user_id=row.user_id,
        key_prefix=row.key_prefix,
        label=row.label,
        scopes=_parse_json(row.scopes_json, []),
        expires_at=row.expires_at,
        last_used_at=row.last_used_at,
        revoked_at=row.revoked_at,
        created_at=row.created_at,
    )


def list_api_keys(db: Session, user_id: str | None = None) -> ApiKeyListOut:
    q = db.query(SecurityApiKey)
    if user_id:
        q = q.filter(SecurityApiKey.user_id == user_id)
    rows = q.order_by(SecurityApiKey.created_at.desc()).all()
    return ApiKeyListOut(items=[_api_key_meta(r) for r in rows], total=len(rows))


def rotate_api_key(db: Session, body: ApiKeyRotateIn, *, created_by: str | None = None) -> ApiKeyRotateOut:
    if not db.get(User, body.user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user_not_found")
    db.query(SecurityApiKey).filter(
        SecurityApiKey.user_id == body.user_id,
        SecurityApiKey.revoked_at.is_(None),
    ).update({"revoked_at": _utcnow()})
    token = secrets.token_urlsafe(24)
    api_key = f"sec_{body.user_id[:8].lower()}_{token}"
    prefix = api_key[:16]
    row = SecurityApiKey(
        id=new_id(),
        user_id=body.user_id,
        key_prefix=prefix,
        key_hash=hash_secret(api_key),
        label=body.label,
        scopes_json=json.dumps(body.scopes),
        created_by=created_by,
        created_at=_utcnow(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    write_audit(db, actor_id=created_by, action="API_KEY_ROTATED", target_type="ApiKey", target_id=row.id, new_state={"user_id": body.user_id})
    return ApiKeyRotateOut(api_key=api_key, meta=_api_key_meta(row))


def list_audit_logs(db: Session, limit: int = 100) -> AuditLogListOut:
    rows = db.query(SecurityAuditLog).order_by(SecurityAuditLog.occurred_at.desc()).limit(limit).all()
    items = []
    for r in rows:
        items.append(
            AuditLogOut(
                id=r.id,
                actor_id=r.actor_id,
                actor_role=r.actor_role,
                action=r.action,
                target_type=r.target_type,
                target_id=r.target_id,
                old_state=_parse_json(r.old_state_json, None),
                new_state=_parse_json(r.new_state_json, None),
                ip_address=r.ip_address,
                user_agent=r.user_agent,
                occurred_at=r.occurred_at,
            )
        )
    return AuditLogListOut(items=items, total=len(items))


def list_domain_links(db: Session, user_id: str | None = None) -> DomainLinkListOut:
    q = db.query(UserDomainLink)
    if user_id:
        q = q.filter(UserDomainLink.user_id == user_id)
    rows = q.order_by(UserDomainLink.created_at.desc()).all()
    items = [
        DomainLinkOut(
            id=r.id,
            user_id=r.user_id,
            domain=r.domain,
            entity_type=r.entity_type,
            entity_id=r.entity_id,
            relation=r.relation,
            is_primary=r.is_primary,
            metadata=_parse_json(r.metadata_json, {}),
            created_at=r.created_at,
        )
        for r in rows
    ]
    return DomainLinkListOut(items=items, total=len(items))


def create_domain_link(db: Session, body: DomainLinkCreateIn) -> DomainLinkOut:
    if not db.get(User, body.user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user_not_found")
    row = UserDomainLink(
        id=new_id(),
        user_id=body.user_id,
        domain=body.domain,
        entity_type=body.entity_type,
        entity_id=body.entity_id,
        relation=body.relation,
        is_primary=body.is_primary,
        metadata_json=json.dumps(body.metadata),
        created_at=_utcnow(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return DomainLinkOut(
        id=row.id,
        user_id=row.user_id,
        domain=row.domain,
        entity_type=row.entity_type,
        entity_id=row.entity_id,
        relation=row.relation,
        is_primary=row.is_primary,
        metadata=body.metadata,
        created_at=row.created_at,
    )


def seed_security_domain(db: Session) -> dict[str, int]:
    counts = {
        "permission_groups": 0,
        "permissions": 0,
        "memberships": 0,
        "webhooks": 0,
        "api_keys": 0,
        "audit_logs": 0,
        "domain_links": 0,
    }
    groups = [
        ("grp-ops-full", "OPS Full Access", "Acesso total operacao lockers", True),
        ("grp-ops-read", "OPS Read Only", "Leitura dashboards e auditoria", True),
        ("grp-partner-api", "Partner API", "Integracoes parceiros webhook", True),
        ("grp-marketplace", "Marketplace Ops", "Magalu Mercado Livre Worten sellers", False),
        ("grp-carriers", "Carriers Global", "InPost DPD DHL USPS locker networks", False),
    ]
    for gid, name, desc, is_sys in groups:
        if not db.get(SecurityPermissionGroup, gid):
            now = _utcnow()
            db.add(
                SecurityPermissionGroup(
                    id=gid,
                    name=name,
                    description=desc,
                    is_system=is_sys,
                    created_at=now,
                    updated_at=now,
                )
            )
            counts["permission_groups"] += 1

    perms = [
        ("grp-ops-full", "ops.lockers.read"),
        ("grp-ops-full", "ops.lockers.write"),
        ("grp-ops-full", "ops.payments.admin"),
        ("grp-ops-read", "ops.dashboard.read"),
        ("grp-partner-api", "partner.webhook.receive"),
        ("grp-marketplace", "marketplace.sellers.manage"),
        ("grp-carriers", "carriers.tracking.read"),
    ]
    for gid, obj in perms:
        exists = (
            db.query(SecurityPermission)
            .filter(SecurityPermission.group_id == gid, SecurityPermission.object_key == obj)
            .first()
        )
        if not exists:
            db.add(SecurityPermission(id=new_id(), group_id=gid, object_key=obj, created_at=_utcnow()))
            counts["permissions"] += 1

    memberships = [
        ("usr-admin-ops", "grp-ops-full", True),
        ("usr-suporte", "grp-ops-read", False),
        ("usr-auditoria", "grp-ops-read", False),
    ]
    for uid, gid, mgr in memberships:
        if not db.get(User, uid):
            continue
        exists = (
            db.query(SecurityPermissionMembership)
            .filter(SecurityPermissionMembership.user_id == uid, SecurityPermissionMembership.group_id == gid)
            .first()
        )
        if not exists:
            db.add(
                SecurityPermissionMembership(
                    id=new_id(),
                    user_id=uid,
                    group_id=gid,
                    is_group_manager=mgr,
                    created_at=_utcnow(),
                )
            )
            counts["memberships"] += 1

    if not db.query(SecurityWebhookEndpoint).filter(SecurityWebhookEndpoint.id == "wh-ops-platform-001").first():
        secret = "dev-webhook-secret-change-me"
        now = _utcnow()
        db.add(
            SecurityWebhookEndpoint(
                id="wh-ops-platform-001",
                owner_type="PLATFORM",
                owner_id=None,
                url="https://hooks.ellanlab.example/ops/security",
                events_json=json.dumps(["user.created", "role.granted", "api_key.rotated"]),
                secret_hash=hash_secret(secret),
                secret_prefix=secret[:8],
                signing_algo="HMAC_SHA256",
                active=True,
                created_at=now,
                updated_at=now,
            )
        )
        counts["webhooks"] += 1

    links = [
        ("usr-admin-ops", "PARTNER", "EcommercePartner", "partner_demo_001", "OWNER"),
        ("usr-admin-ops", "MARKETPLACE", "Seller", "seller-magalu-demo", "ADMIN"),
        ("usr-suporte", "LOCKER", "Locker", "locker-inpost-br-001", "SUPPORT"),
        ("usr-auditoria", "PAYMENT", "PaymentProvider", "psp-stripe-demo", "AUDITOR"),
    ]
    for uid, domain, etype, eid, rel in links:
        if not db.get(User, uid):
            continue
        exists = (
            db.query(UserDomainLink)
            .filter(
                UserDomainLink.user_id == uid,
                UserDomainLink.domain == domain,
                UserDomainLink.entity_type == etype,
                UserDomainLink.entity_id == eid,
            )
            .first()
        )
        if not exists:
            db.add(
                UserDomainLink(
                    id=new_id(),
                    user_id=uid,
                    domain=domain,
                    entity_type=etype,
                    entity_id=eid,
                    relation=rel,
                    is_primary=domain == "PARTNER",
                    metadata_json=json.dumps({"seed": True}),
                    created_at=_utcnow(),
                )
            )
            counts["domain_links"] += 1

    if db.query(SecurityAuditLog).count() == 0:
        write_audit(
            db,
            actor_id="usr-admin-ops",
            actor_role="admin_operacao",
            action="SECURITY_DOMAIN_SEEDED",
            target_type="Platform",
            target_id="ellanlab",
            new_state={"carriers": ["InPost", "DPD", "DHL"], "marketplaces": ["Magalu", "Mercado Livre"]},
        )
        counts["audit_logs"] += 1

    from app.services.security_professional_service import seed_professional_layer

    counts["professional"] = seed_professional_layer(db)

    db.commit()
    return counts
