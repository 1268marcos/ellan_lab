from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.security import (
    ApiKeyListOut,
    ApiKeyRotateIn,
    ApiKeyRotateOut,
    AuditLogListOut,
    CrossDomainGrantCreateIn,
    CrossDomainGrantListOut,
    CrossDomainGrantOut,
    DomainCatalogListOut,
    DomainHealthListOut,
    DomainLinkCreateIn,
    DomainLinkListOut,
    DomainLinkOut,
    EcosystemMapOut,
    IdentityProviderListOut,
    MembershipCreateIn,
    MembershipListOut,
    MembershipOut,
    PermissionCreateIn,
    PermissionGroupCreateIn,
    PermissionGroupListOut,
    PermissionGroupOut,
    PermissionListOut,
    PermissionOut,
    PolicySnapshotCreateIn,
    PolicySnapshotListOut,
    PolicySnapshotOut,
    RoleCatalogListOut,
    LockerPlayerListOut,
    LockerPlayerSecurityProfileOut,
    UserPlayerAccessCreateIn,
    UserPlayerAccessListOut,
    UserPlayerAccessOut,
    PlayerSegmentListOut,
    PlayerRelationListOut,
    PlayerIntegrationListOut,
    EcosystemTaxonomySummaryOut,
    SecuritySummaryOut,
    SessionListOut,
    User360Out,
    WebhookDeliveryListOut,
    WebhookEndpointCreateIn,
    WebhookEndpointListOut,
    WebhookEndpointOut,
    WebhookRotateOut,
)
from app.services import security_locker_players_service, security_professional_service, security_service

router = APIRouter(prefix="/security-admin", tags=["security-admin"])


@router.get("/summary", response_model=SecuritySummaryOut)
def summary(db: Session = Depends(get_db)) -> SecuritySummaryOut:
    return security_service.get_summary(db)


@router.get("/permission-groups", response_model=PermissionGroupListOut)
def list_groups(db: Session = Depends(get_db)) -> PermissionGroupListOut:
    return security_service.list_permission_groups(db)


@router.post("/permission-groups", response_model=PermissionGroupOut, status_code=status.HTTP_201_CREATED)
def create_group(body: PermissionGroupCreateIn, db: Session = Depends(get_db)) -> PermissionGroupOut:
    return security_service.create_permission_group(db, body)


@router.get("/permissions", response_model=PermissionListOut)
def list_permissions(
    group_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> PermissionListOut:
    return security_service.list_permissions(db, group_id)


@router.post("/permissions", response_model=PermissionOut, status_code=status.HTTP_201_CREATED)
def create_permission(body: PermissionCreateIn, db: Session = Depends(get_db)) -> PermissionOut:
    return security_service.create_permission(db, body)


@router.get("/permission-memberships", response_model=MembershipListOut)
def list_memberships(
    user_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> MembershipListOut:
    return security_service.list_memberships(db, user_id)


@router.post("/permission-memberships", response_model=MembershipOut, status_code=status.HTTP_201_CREATED)
def create_membership(body: MembershipCreateIn, db: Session = Depends(get_db)) -> MembershipOut:
    return security_service.create_membership(db, body)


@router.get("/webhook-endpoints", response_model=WebhookEndpointListOut)
def list_webhooks(db: Session = Depends(get_db)) -> WebhookEndpointListOut:
    return security_service.list_webhooks(db)


@router.post("/webhook-endpoints", response_model=WebhookEndpointOut, status_code=status.HTTP_201_CREATED)
def create_webhook(body: WebhookEndpointCreateIn, db: Session = Depends(get_db)) -> WebhookEndpointOut:
    out, _secret = security_service.create_webhook(db, body)
    return out


@router.post("/webhook-endpoints/{endpoint_id}/rotate-secret", response_model=WebhookRotateOut)
def rotate_webhook(endpoint_id: str, db: Session = Depends(get_db)) -> WebhookRotateOut:
    return security_service.rotate_webhook_secret(db, endpoint_id)


@router.get("/api-keys", response_model=ApiKeyListOut)
def list_api_keys(
    user_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> ApiKeyListOut:
    return security_service.list_api_keys(db, user_id)


@router.post("/api-keys/rotate", response_model=ApiKeyRotateOut)
def rotate_api_key(body: ApiKeyRotateIn, db: Session = Depends(get_db)) -> ApiKeyRotateOut:
    return security_service.rotate_api_key(db, body, created_by=body.user_id)


@router.get("/audit-logs", response_model=AuditLogListOut)
def list_audit(
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> AuditLogListOut:
    return security_service.list_audit_logs(db, limit)


@router.get("/domain-links", response_model=DomainLinkListOut)
def list_domain_links(
    user_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> DomainLinkListOut:
    return security_service.list_domain_links(db, user_id)


@router.post("/domain-links", response_model=DomainLinkOut, status_code=status.HTTP_201_CREATED)
def create_domain_link(body: DomainLinkCreateIn, db: Session = Depends(get_db)) -> DomainLinkOut:
    return security_service.create_domain_link(db, body)


@router.get("/domain-catalog", response_model=DomainCatalogListOut)
def domain_catalog(db: Session = Depends(get_db)) -> DomainCatalogListOut:
    return security_professional_service.list_domain_catalog(db)


@router.get("/role-catalog", response_model=RoleCatalogListOut)
def role_catalog(db: Session = Depends(get_db)) -> RoleCatalogListOut:
    return security_professional_service.list_role_catalog(db)


@router.get("/cross-domain/health", response_model=DomainHealthListOut)
def cross_domain_health(db: Session = Depends(get_db)) -> DomainHealthListOut:
    return security_professional_service.probe_domain_health(db)


@router.get("/cross-domain/ecosystem-map", response_model=EcosystemMapOut)
def ecosystem_map(db: Session = Depends(get_db)) -> EcosystemMapOut:
    return security_professional_service.build_ecosystem_map(db)


@router.get("/cross-domain-grants", response_model=CrossDomainGrantListOut)
def list_grants(
    user_id: Optional[str] = Query(None),
    domain_code: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> CrossDomainGrantListOut:
    return security_professional_service.list_cross_domain_grants(db, user_id, domain_code)


@router.post("/cross-domain-grants", response_model=CrossDomainGrantOut, status_code=status.HTTP_201_CREATED)
def create_grant(body: CrossDomainGrantCreateIn, db: Session = Depends(get_db)) -> CrossDomainGrantOut:
    return security_professional_service.create_cross_domain_grant(db, body)


@router.get("/users/{user_id}/360", response_model=User360Out)
def user_360(user_id: str, db: Session = Depends(get_db)) -> User360Out:
    return security_professional_service.get_user_360(db, user_id)


@router.get("/sessions", response_model=SessionListOut)
def list_sessions(
    user_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> SessionListOut:
    return security_professional_service.list_sessions(db, user_id)


@router.get("/webhook-deliveries", response_model=WebhookDeliveryListOut)
def list_deliveries(
    endpoint_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> WebhookDeliveryListOut:
    return security_professional_service.list_webhook_deliveries(db, endpoint_id)


@router.get("/identity-providers", response_model=IdentityProviderListOut)
def list_idps(db: Session = Depends(get_db)) -> IdentityProviderListOut:
    return security_professional_service.list_identity_providers(db)


@router.get("/policy-snapshots", response_model=PolicySnapshotListOut)
def list_policies(db: Session = Depends(get_db)) -> PolicySnapshotListOut:
    return security_professional_service.list_policy_snapshots(db)


@router.post("/policy-snapshots", response_model=PolicySnapshotOut, status_code=status.HTTP_201_CREATED)
def create_policy(body: PolicySnapshotCreateIn, db: Session = Depends(get_db)) -> PolicySnapshotOut:
    return security_professional_service.create_policy_snapshot(db, body)


@router.get("/ecosystem-taxonomy/summary", response_model=EcosystemTaxonomySummaryOut)
def ecosystem_taxonomy_summary(db: Session = Depends(get_db)) -> EcosystemTaxonomySummaryOut:
    return security_locker_players_service.get_ecosystem_taxonomy_summary(db)


@router.get("/player-segments", response_model=PlayerSegmentListOut)
def list_player_segments(db: Session = Depends(get_db)) -> PlayerSegmentListOut:
    return security_locker_players_service.list_player_segments(db)


@router.get("/player-relations", response_model=PlayerRelationListOut)
def list_player_relations(
    from_code: Optional[str] = Query(None),
    to_code: Optional[str] = Query(None),
    relation_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> PlayerRelationListOut:
    return security_locker_players_service.list_player_relations(db, from_code=from_code, to_code=to_code, relation_type=relation_type)


@router.get("/player-integrations", response_model=PlayerIntegrationListOut)
def list_player_integrations(
    player_code: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> PlayerIntegrationListOut:
    return security_locker_players_service.list_player_integrations(db, player_code)


@router.get("/locker-players", response_model=LockerPlayerListOut)
def list_locker_players(
    priority_only: bool = Query(False),
    segment: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> LockerPlayerListOut:
    return security_locker_players_service.list_locker_players(db, priority_only=priority_only, segment=segment)


@router.get("/locker-players/priority", response_model=LockerPlayerListOut)
def list_priority_locker_players(db: Session = Depends(get_db)) -> LockerPlayerListOut:
    return security_locker_players_service.list_locker_players(db, priority_only=True)


@router.get("/locker-players/{player_code}/security-profile", response_model=LockerPlayerSecurityProfileOut)
def locker_player_profile(player_code: str, db: Session = Depends(get_db)) -> LockerPlayerSecurityProfileOut:
    return security_locker_players_service.get_player_security_profile(db, player_code)


@router.post("/locker-players/sync-registry")
def sync_locker_registry(db: Session = Depends(get_db)) -> dict:
    return security_locker_players_service.sync_locker_player_registry(db)


@router.get("/user-player-access", response_model=UserPlayerAccessListOut)
def list_user_player_access(
    user_id: Optional[str] = Query(None),
    player_code: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> UserPlayerAccessListOut:
    return security_locker_players_service.list_user_player_access(db, user_id, player_code)


@router.post("/user-player-access", response_model=UserPlayerAccessOut, status_code=status.HTTP_201_CREATED)
def create_user_player_access(body: UserPlayerAccessCreateIn, db: Session = Depends(get_db)) -> UserPlayerAccessOut:
    return security_locker_players_service.create_user_player_access(db, body)


@router.post("/seed")
def seed_security(db: Session = Depends(get_db)) -> dict:
    from app.services.seed_data import run_seed

    base = run_seed(db)
    sec = security_service.seed_security_domain(db)
    return {"base": base, "security": sec}
