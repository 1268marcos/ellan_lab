from __future__ import annotations

import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.clients.domain_http import DomainHttpError, fetch_items, fetch_json
from app.core.config import get_settings
from app.models.security import (
    SecurityCrossDomainGrant,
    SecurityDomainCatalog,
    SecurityIdentityProvider,
    SecurityPermission,
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
    CrossDomainGrantCreateIn,
    CrossDomainGrantListOut,
    CrossDomainGrantOut,
    DomainCatalogListOut,
    DomainCatalogOut,
    DomainHealthListOut,
    DomainHealthOut,
    DomainLinkOut,
    EcosystemEntityOut,
    EcosystemMapOut,
    IdentityProviderListOut,
    IdentityProviderOut,
    PolicySnapshotCreateIn,
    PolicySnapshotListOut,
    PolicySnapshotOut,
    RoleCatalogListOut,
    RoleCatalogOut,
    SessionListOut,
    SessionOut,
    User360Out,
    WebhookDeliveryListOut,
    WebhookDeliveryOut,
)
from app.services.crypto_util import hash_secret, new_id
from app.services.security_service import _parse_json, _utcnow, write_audit


def _domain_out(row: SecurityDomainCatalog) -> DomainCatalogOut:
    return DomainCatalogOut(
        code=row.code,
        label=row.label,
        description=row.description,
        admin_route=row.admin_route,
        sort_order=row.sort_order,
        is_active=row.is_active,
        regions=_parse_json(row.regions_json, []),
    )


def list_domain_catalog(db: Session) -> DomainCatalogListOut:
    rows = db.query(SecurityDomainCatalog).filter(SecurityDomainCatalog.is_active.is_(True)).order_by(SecurityDomainCatalog.sort_order).all()
    return DomainCatalogListOut(items=[_domain_out(r) for r in rows], total=len(rows))


def list_role_catalog(db: Session) -> RoleCatalogListOut:
    rows = db.query(SecurityRoleCatalog).order_by(SecurityRoleCatalog.sort_order).all()
    items = [
        RoleCatalogOut(
            code=r.code,
            label=r.label,
            description=r.description,
            default_scope_type=r.default_scope_type,
            allowed_domains=_parse_json(r.allowed_domains_json, []),
            is_system=r.is_system,
        )
        for r in rows
    ]
    return RoleCatalogListOut(items=items, total=len(items))


def probe_domain_health(db: Session) -> DomainHealthListOut:
    s = get_settings()
    base_urls = {
        "PARTNER": s.partner_admin_base_url,
        "PAYMENT_GATEWAY": s.payment_gateway_admin_url,
        "MARKETPLACE": s.marketplace_admin_url,
        "HARDWARE": s.hardware_admin_url,
        "ORDER_PICKUP": s.order_pickup_admin_url,
        "FINANCE": s.finance_admin_url,
        "PAYMENTS": s.payments_admin_url,
        "ML": s.ml_admin_url,
    }

    rows = db.query(SecurityDomainCatalog).filter(SecurityDomainCatalog.is_active.is_(True)).order_by(SecurityDomainCatalog.sort_order).all()
    if not rows:
        rows = []

    items: list[DomainHealthOut] = []
    for row in rows:
        base = base_urls.get(row.code)
        reachable = False
        detail: str | None = None
        if base and row.health_path:
            url = f"{base}{row.health_path}"
            try:
                fetch_json(row.code, url)
                reachable = True
            except DomainHttpError as exc:
                detail = exc.detail
        elif row.code == "PARTNER":
            reachable = True
        items.append(
            DomainHealthOut(
                domain=row.code,
                label=row.label,
                reachable=reachable,
                detail=detail,
                admin_route=row.admin_route,
            )
        )
    reachable_count = sum(1 for i in items if i.reachable)
    return DomainHealthListOut(items=items, reachable_count=reachable_count, total=len(items))


def list_cross_domain_grants(db: Session, user_id: str | None = None, domain_code: str | None = None) -> CrossDomainGrantListOut:
    q = db.query(SecurityCrossDomainGrant).filter(SecurityCrossDomainGrant.is_active.is_(True))
    if user_id:
        q = q.filter(SecurityCrossDomainGrant.user_id == user_id)
    if domain_code:
        q = q.filter(SecurityCrossDomainGrant.domain_code == domain_code)
    rows = q.order_by(SecurityCrossDomainGrant.created_at.desc()).all()
    return CrossDomainGrantListOut(items=[CrossDomainGrantOut.model_validate(r) for r in rows], total=len(rows))


def create_cross_domain_grant(db: Session, body: CrossDomainGrantCreateIn, *, granted_by: str | None = None) -> CrossDomainGrantOut:
    if not db.get(User, body.user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user_not_found")
    row = SecurityCrossDomainGrant(
        id=new_id(),
        user_id=body.user_id,
        domain_code=body.domain_code,
        entity_type=body.entity_type,
        entity_id=body.entity_id,
        entity_label=body.entity_label,
        permission_key=body.permission_key,
        scope_type=body.scope_type,
        granted_by=granted_by,
        expires_at=body.expires_at,
        is_active=True,
        metadata_json=json.dumps(body.metadata),
        created_at=_utcnow(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    write_audit(
        db,
        actor_id=granted_by,
        action="CROSS_DOMAIN_GRANT_CREATED",
        target_type="CrossDomainGrant",
        target_id=row.id,
        new_state={"domain": row.domain_code, "permission": row.permission_key},
    )
    return CrossDomainGrantOut.model_validate(row)


def build_ecosystem_map(db: Session) -> EcosystemMapOut:
    entities: list[EcosystemEntityOut] = []

    for link in db.query(UserDomainLink).limit(200).all():
        entities.append(
            EcosystemEntityOut(
                domain=link.domain,
                entity_type=link.entity_type,
                entity_id=link.entity_id,
                label=f"{link.relation}",
                source="user_domain_links",
            )
        )

    for grant in db.query(SecurityCrossDomainGrant).filter(SecurityCrossDomainGrant.is_active.is_(True)).limit(200).all():
        entities.append(
            EcosystemEntityOut(
                domain=grant.domain_code,
                entity_type=grant.entity_type,
                entity_id=grant.entity_id,
                label=grant.entity_label or grant.permission_key,
                source="cross_domain_grants",
            )
        )

    try:
        from app.services.security_locker_players_service import locker_players_for_ecosystem_map

        for lp in locker_players_for_ecosystem_map(db):
            entities.append(
                EcosystemEntityOut(
                    domain=lp["domain"],
                    entity_type=lp["entity_type"],
                    entity_id=lp["entity_id"],
                    label=lp["label"],
                    source=lp["source"],
                )
            )
    except Exception:
        pass

    remote = 0
    s = get_settings()
    try:
        players = fetch_items(
            "PARTNER",
            f"{get_settings().partner_admin_base_url}/api/v1/partner-admin/ecosystem/players",
            params={"limit": 30},
        )
        for p in players[:30]:
            code = str(p.get("player_code") or p.get("code") or "")
            if code:
                entities.append(
                    EcosystemEntityOut(
                        domain="PARTNER",
                        entity_type="EcosystemPlayer",
                        entity_id=code,
                        label=str(p.get("name") or code),
                        source="partner_ecosystem",
                    )
                )
                remote += 1
    except DomainHttpError:
        pass

    try:
        channels = fetch_items("MARKETPLACE", f"{s.marketplace_admin_url}/api/v1/marketplace-admin/channel-partners")
        for c in channels[:20]:
            cid = str(c.get("id") or c.get("code") or "")
            if cid:
                entities.append(
                    EcosystemEntityOut(
                        domain="MARKETPLACE",
                        entity_type="ChannelPartner",
                        entity_id=cid,
                        label=str(c.get("name") or c.get("code") or cid),
                        source="marketplace_admin",
                    )
                )
                remote += 1
    except DomainHttpError:
        pass

    domains = db.query(SecurityDomainCatalog).count()
    return EcosystemMapOut(entities=entities, domains_probed=domains, remote_entities=remote)


def get_user_360(db: Session, user_id: str) -> User360Out:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user_not_found")

    roles = [
        r.role
        for r in db.query(UserRole)
        .filter(UserRole.user_id == user_id, UserRole.is_active.is_(True), UserRole.revoked_at.is_(None))
        .all()
    ]
    group_ids = [m.group_id for m in db.query(SecurityPermissionMembership).filter(SecurityPermissionMembership.user_id == user_id).all()]
    groups = [g.name for g in db.query(SecurityPermissionGroup).filter(SecurityPermissionGroup.id.in_(group_ids)).all()] if group_ids else []

    links = [
        DomainLinkOut(
            id=l.id,
            user_id=l.user_id,
            domain=l.domain,
            entity_type=l.entity_type,
            entity_id=l.entity_id,
            relation=l.relation,
            is_primary=l.is_primary,
            metadata=_parse_json(l.metadata_json, {}),
            created_at=l.created_at,
        )
        for l in db.query(UserDomainLink).filter(UserDomainLink.user_id == user_id).all()
    ]
    grants = list_cross_domain_grants(db, user_id=user_id).items
    sessions = (
        db.query(SecurityUserSession)
        .filter(SecurityUserSession.user_id == user_id, SecurityUserSession.revoked_at.is_(None))
        .count()
    )

    remote_refs: list[EcosystemEntityOut] = []
    for g in grants:
        remote_refs.append(
            EcosystemEntityOut(
                domain=g.domain_code,
                entity_type=g.entity_type,
                entity_id=g.entity_id,
                label=g.entity_label or g.permission_key,
                source="grant",
            )
        )

    return User360Out(
        user_id=user.id,
        full_name=user.full_name,
        email=user.email,
        roles=roles,
        permission_groups=groups,
        domain_links=links,
        cross_domain_grants=grants,
        active_sessions=sessions,
        remote_refs=remote_refs,
    )


def list_sessions(db: Session, user_id: str | None = None) -> SessionListOut:
    q = db.query(SecurityUserSession)
    if user_id:
        q = q.filter(SecurityUserSession.user_id == user_id)
    rows = q.order_by(SecurityUserSession.created_at.desc()).limit(200).all()
    return SessionListOut(items=[SessionOut.model_validate(r) for r in rows], total=len(rows))


def list_webhook_deliveries(db: Session, endpoint_id: str | None = None) -> WebhookDeliveryListOut:
    q = db.query(SecurityWebhookDelivery)
    if endpoint_id:
        q = q.filter(SecurityWebhookDelivery.endpoint_id == endpoint_id)
    rows = q.order_by(SecurityWebhookDelivery.created_at.desc()).limit(200).all()
    return WebhookDeliveryListOut(items=[WebhookDeliveryOut.model_validate(r) for r in rows], total=len(rows))


def list_identity_providers(db: Session) -> IdentityProviderListOut:
    rows = db.query(SecurityIdentityProvider).order_by(SecurityIdentityProvider.name).all()
    items = [
        IdentityProviderOut(
            code=r.code,
            name=r.name,
            provider_type=r.provider_type,
            issuer_url=r.issuer_url,
            is_active=r.is_active,
            allowed_domains=_parse_json(r.allowed_domains_json, []),
        )
        for r in rows
    ]
    return IdentityProviderListOut(items=items, total=len(items))


def list_policy_snapshots(db: Session) -> PolicySnapshotListOut:
    rows = db.query(SecurityPolicySnapshot).order_by(SecurityPolicySnapshot.created_at.desc()).limit(50).all()
    items = []
    for r in rows:
        snap = _parse_json(r.snapshot_json, {})
        items.append(
            PolicySnapshotOut(
                id=r.id,
                version_label=r.version_label,
                policy_kind=r.policy_kind,
                remark=r.remark,
                created_by=r.created_by,
                created_at=r.created_at,
                groups_count=int(snap.get("groups_count") or 0),
                permissions_count=int(snap.get("permissions_count") or 0),
            )
        )
    return PolicySnapshotListOut(items=items, total=len(items))


def create_policy_snapshot(db: Session, body: PolicySnapshotCreateIn) -> PolicySnapshotOut:
    groups = db.query(SecurityPermissionGroup).count()
    perms = db.query(SecurityPermission).count()
    snap = {
        "groups_count": groups,
        "permissions_count": perms,
        "roles_catalog": db.query(SecurityRoleCatalog).count(),
        "domains": [r.code for r in db.query(SecurityDomainCatalog).all()],
        "captured_at": _utcnow().isoformat(),
    }
    row = SecurityPolicySnapshot(
        id=new_id(),
        version_label=body.version_label,
        policy_kind=body.policy_kind,
        snapshot_json=json.dumps(snap),
        created_by=body.created_by,
        remark=body.remark,
        created_at=_utcnow(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return PolicySnapshotOut(
        id=row.id,
        version_label=row.version_label,
        policy_kind=row.policy_kind,
        remark=row.remark,
        created_by=row.created_by,
        created_at=row.created_at,
        groups_count=groups,
        permissions_count=perms,
    )


def seed_professional_layer(db: Session) -> dict[str, int]:
    counts = {
        "domain_catalog": 0,
        "role_catalog": 0,
        "cross_domain_grants": 0,
        "sessions": 0,
        "webhook_deliveries": 0,
        "identity_providers": 0,
        "policy_snapshots": 0,
    }
    now = _utcnow()

    domains = [
        ("PARTNER", "Parceiros & Ecossistema", "InPost DPD Magalu integrações", "/ops/partners/admin", "/api/v1/partner-admin/health", 10, '["BR","EU","US"]'),
        ("MARKETPLACE", "Marketplace", "Magalu Mercado Livre Amazon sellers", "/ops/marketplace/admin", "/api/v1/marketplace-admin/health", 20, '["BR","EU"]'),
        ("PAYMENT_GATEWAY", "Payment Gateway", "PSP PIX cartão SwipBox lockers", "/ops/payment-gateway/admin", "/api/v1/payment-gateway-admin/health", 30, '["GLOBAL"]'),
        ("PAYMENTS", "Payments OPS", "Ledger splits conciliação", "/ops/payments/admin", "/api/v1/payments-admin/health", 35, '["GLOBAL"]'),
        ("HARDWARE", "Hardware OPS", "SwipBox Cleveron InPost rede locker", "/ops/hardware/admin", "/api/v1/hardware-admin/health", 40, '["GLOBAL"]'),
        ("ORDER_PICKUP", "Order Pickup", "Pedidos manifestos pickup", "/ops/order-pickup/admin", "/api/v1/order-pickup-admin/health", 50, '["BR"]'),
        ("FINANCE", "Finance", "CAPEX OPEX repasses", "/ops/finance/admin", "/api/v1/finance-admin/health", 60, '["BR"]'),
        ("ML", "ML OPS", "Predição fraude LTV", "/ops/ml/admin", "/api/v1/ml-admin/health", 70, '["GLOBAL"]'),
        ("BI_ANALYTICS", "BI & Analytics", "Facts marts KPIs InPost DHL Magalu", "/ops/bi-analytics/admin", "/api/v1/analytics-bi-admin/health", 72, '["GLOBAL"]'),
        ("TENANT", "Tenants", "Multi-tenant fiscal domínios", "/ops/tenants/admin", None, 80, '["BR"]'),
        ("CARRIER", "Carriers", "DHL DPD Correios CTT USPS Royal Mail Colissimo", None, None, 90, '["GLOBAL"]'),
    ]
    for code, label, desc, route, health, order, regions in domains:
        if not db.get(SecurityDomainCatalog, code):
            db.add(
                SecurityDomainCatalog(
                    code=code,
                    label=label,
                    description=desc,
                    admin_route=route,
                    health_path=health,
                    sort_order=order,
                    is_active=True,
                    regions_json=regions,
                    metadata_json="{}",
                    created_at=now,
                )
            )
            counts["domain_catalog"] += 1

    roles = [
        ("admin_operacao", "Admin Operação", "Acesso total OPS lockers pagamentos", "GLOBAL", '["PARTNER","MARKETPLACE","PAYMENT_GATEWAY","HARDWARE","ORDER_PICKUP"]', 10),
        ("suporte", "Suporte", "Leitura e ações limitadas suporte", "GLOBAL", '["ORDER_PICKUP","HARDWARE"]', 20),
        ("auditoria", "Auditoria", "Somente leitura auditoria compliance", "GLOBAL", '["PARTNER","PAYMENTS","FINANCE"]', 30),
        ("usuario_comum", "Usuário comum", "App consumidor final", "GLOBAL", "[]", 40),
        ("partner_api", "Partner API", "Integração B2B parceiro", "PARTNER", '["PARTNER"]', 50),
        ("marketplace_seller", "Seller Marketplace", "Gestão seller Magalu ML", "SELLER", '["MARKETPLACE"]', 60),
        ("carrier_ops", "Carrier OPS", "Operador rede locker InPost DPD", "NETWORK", '["CARRIER","HARDWARE"]', 70),
    ]
    for code, label, desc, scope, allowed, order in roles:
        if not db.get(SecurityRoleCatalog, code):
            db.add(
                SecurityRoleCatalog(
                    code=code,
                    label=label,
                    description=desc,
                    default_scope_type=scope,
                    allowed_domains_json=allowed,
                    is_system=True,
                    sort_order=order,
                    created_at=now,
                )
            )
            counts["role_catalog"] += 1

    grant_seed = [
        ("usr-admin-ops", "HARDWARE", "EcosystemPlayer", "INPOST", "InPost Parcel Lockers", "ops.hardware.admin", "NETWORK"),
        ("usr-admin-ops", "MARKETPLACE", "ChannelPartner", "MAGALU", "Magalu Marketplace", "marketplace.sellers.write", "CHANNEL"),
        ("usr-admin-ops", "PAYMENT_GATEWAY", "PaymentProvider", "STRIPE", "Stripe PSP", "payments.psp.configure", "PROVIDER"),
        ("usr-suporte", "ORDER_PICKUP", "Order", "order-demo-001", "Pedido demo suporte", "orders.read", "ENTITY"),
        ("usr-auditoria", "FINANCE", "SettlementBatch", "batch-demo-001", "Lote auditoria", "finance.audit.read", "ENTITY"),
        ("usr-auditoria", "CARRIER", "CarrierNetwork", "DPD", "DPD Locker Network", "carriers.audit", "NETWORK"),
    ]
    for uid, domain, etype, eid, label, perm, scope in grant_seed:
        if not db.get(User, uid):
            continue
        exists = (
            db.query(SecurityCrossDomainGrant)
            .filter(
                SecurityCrossDomainGrant.user_id == uid,
                SecurityCrossDomainGrant.domain_code == domain,
                SecurityCrossDomainGrant.entity_id == eid,
                SecurityCrossDomainGrant.permission_key == perm,
            )
            .first()
        )
        if not exists:
            db.add(
                SecurityCrossDomainGrant(
                    id=new_id(),
                    user_id=uid,
                    domain_code=domain,
                    entity_type=etype,
                    entity_id=eid,
                    entity_label=label,
                    permission_key=perm,
                    scope_type=scope,
                    granted_by="usr-admin-ops",
                    is_active=True,
                    metadata_json=json.dumps({"seed": True, "tier": "professional"}),
                    created_at=now,
                )
            )
            counts["cross_domain_grants"] += 1

    idps = [
        ("okta-ellan", "Okta Ellan OPS", "OIDC", "https://ellanlab.okta.com/oauth2/default", "secret/okta-client"),
        ("azure-ad", "Azure AD Enterprise", "OIDC", "https://login.microsoftonline.com/ellanlab/v2.0", "secret/azure-client"),
        ("google-workspace", "Google Workspace", "OIDC", "https://accounts.google.com", "secret/google-client"),
    ]
    for code, name, ptype, issuer, cref in idps:
        if not db.get(SecurityIdentityProvider, code):
            db.add(
                SecurityIdentityProvider(
                    code=code,
                    name=name,
                    provider_type=ptype,
                    issuer_url=issuer,
                    client_id_ref=cref,
                    allowed_domains_json='["PARTNER","MARKETPLACE"]',
                    is_active=code == "okta-ellan",
                    metadata_json="{}",
                    created_at=now,
                )
            )
            counts["identity_providers"] += 1

    for uid in ("usr-admin-ops", "usr-suporte"):
        if not db.get(User, uid):
            continue
        active = (
            db.query(SecurityUserSession)
            .filter(SecurityUserSession.user_id == uid, SecurityUserSession.revoked_at.is_(None))
            .first()
        )
        if not active:
            token = secrets.token_urlsafe(32)
            db.add(
                SecurityUserSession(
                    id=new_id(),
                    user_id=uid,
                    session_token_hash=hash_secret(token),
                    user_agent="OPS-Console/seed",
                    ip_address="127.0.0.1",
                    auth_method="SSO" if uid == "usr-admin-ops" else "API_KEY",
                    identity_provider_code="okta-ellan" if uid == "usr-admin-ops" else None,
                    created_at=now,
                    expires_at=now + timedelta(days=7),
                    last_seen_at=now,
                )
            )
            counts["sessions"] += 1

    wh = db.query(SecurityWebhookEndpoint).first()
    if wh and not db.query(SecurityWebhookDelivery).filter(SecurityWebhookDelivery.id == "whd-seed-001").first():
        db.add(
            SecurityWebhookDelivery(
                id="whd-seed-001",
                endpoint_id=wh.id,
                event_name="user.created",
                aggregate_type="User",
                aggregate_id="usr-admin-ops",
                payload_json=json.dumps({"event": "user.created", "user_id": "usr-admin-ops"}),
                status="DELIVERED",
                attempt_count=1,
                last_status_code=200,
                delivered_at=now,
                created_at=now,
            )
        )
        counts["webhook_deliveries"] += 1

    if not db.query(SecurityPolicySnapshot).filter(SecurityPolicySnapshot.version_label == "v2026.05-professional").first():
        groups = db.query(SecurityPermissionGroup).count()
        perms = db.query(SecurityPermission).count()
        db.add(
            SecurityPolicySnapshot(
                id=new_id(),
                version_label="v2026.05-professional",
                policy_kind="RBAC",
                snapshot_json=json.dumps({"groups_count": groups, "permissions_count": perms, "tier": "worldwide"}),
                created_by="usr-admin-ops",
                remark="Baseline mundial InPost DHL Magalu MercadoLivre Amazon DPD Correios CTT Worten El Corte Inglés",
                created_at=now,
            )
        )
        counts["policy_snapshots"] += 1

    from app.services.security_locker_players_service import (
        seed_player_cross_domain_grants,
        sync_locker_player_registry,
    )

    counts["locker_registry"] = sync_locker_player_registry(db)
    from app.services.security_locker_players_service import seed_ecosystem_taxonomy

    counts["ecosystem_taxonomy"] = seed_ecosystem_taxonomy(db)
    counts["locker_player_bindings"] = seed_player_cross_domain_grants(db)

    from app.services.security_value_service import seed_value_layer

    counts["value_layer"] = seed_value_layer(db)

    db.commit()
    return counts
