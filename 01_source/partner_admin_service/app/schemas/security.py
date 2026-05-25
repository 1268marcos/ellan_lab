from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class SecuritySummaryOut(BaseModel):
    users: int
    active_roles: int
    permission_groups: int
    webhook_endpoints: int
    active_api_keys: int
    audit_logs: int
    domain_links: int
    domain_catalog: int = 0
    role_catalog: int = 0
    cross_domain_grants: int = 0
    active_sessions: int = 0
    webhook_deliveries: int = 0
    identity_providers: int = 0
    policy_snapshots: int = 0
    domains_reachable: int = 0
    domains_total: int = 0
    locker_players: int = 0
    user_player_access: int = 0


class UserCreateIn(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    email: str = Field(min_length=3, max_length=255)
    phone: Optional[str] = None
    is_active: bool = True
    email_verified: bool = False


class UserUpdateIn(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None
    email_verified: Optional[bool] = None


class PermissionGroupCreateIn(BaseModel):
    name: str
    description: Optional[str] = None


class PermissionGroupOut(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    is_system: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class PermissionGroupListOut(BaseModel):
    items: list[PermissionGroupOut]
    total: int


class PermissionCreateIn(BaseModel):
    group_id: str
    object_key: str


class PermissionOut(BaseModel):
    id: str
    group_id: str
    object_key: str
    created_at: datetime

    model_config = {"from_attributes": True}


class PermissionListOut(BaseModel):
    items: list[PermissionOut]
    total: int


class MembershipCreateIn(BaseModel):
    user_id: str
    group_id: str
    is_group_manager: bool = False


class MembershipOut(BaseModel):
    id: str
    user_id: str
    group_id: str
    is_group_manager: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class MembershipListOut(BaseModel):
    items: list[MembershipOut]
    total: int


class WebhookEndpointCreateIn(BaseModel):
    url: str
    owner_type: str = "PLATFORM"
    owner_id: Optional[str] = None
    events: list[str] = Field(default_factory=lambda: ["*"])
    signing_algo: str = "HMAC_SHA256"
    active: bool = True


class WebhookEndpointOut(BaseModel):
    id: str
    owner_type: str
    owner_id: Optional[str] = None
    url: str
    events: list[str]
    secret_prefix: Optional[str] = None
    signing_algo: str
    active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WebhookEndpointListOut(BaseModel):
    items: list[WebhookEndpointOut]
    total: int


class WebhookRotateOut(BaseModel):
    endpoint_id: str
    secret_prefix: str
    webhook_secret: str


class ApiKeyRotateIn(BaseModel):
    user_id: str
    label: Optional[str] = "ops-console"
    scopes: list[str] = Field(default_factory=lambda: ["ops:read", "ops:write"])


class ApiKeyMetaOut(BaseModel):
    id: str
    user_id: str
    key_prefix: str
    label: Optional[str] = None
    scopes: list[str]
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ApiKeyRotateOut(BaseModel):
    api_key: str
    meta: ApiKeyMetaOut


class ApiKeyListOut(BaseModel):
    items: list[ApiKeyMetaOut]
    total: int


class AuditLogOut(BaseModel):
    id: str
    actor_id: Optional[str] = None
    actor_role: Optional[str] = None
    action: str
    target_type: str
    target_id: str
    old_state: Optional[dict[str, Any]] = None
    new_state: Optional[dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    occurred_at: datetime

    model_config = {"from_attributes": True}


class AuditLogListOut(BaseModel):
    items: list[AuditLogOut]
    total: int


class DomainLinkCreateIn(BaseModel):
    user_id: str
    domain: str
    entity_type: str
    entity_id: str
    relation: str = "MEMBER"
    is_primary: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class DomainLinkOut(BaseModel):
    id: str
    user_id: str
    domain: str
    entity_type: str
    entity_id: str
    relation: str
    is_primary: bool
    metadata: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


class DomainLinkListOut(BaseModel):
    items: list[DomainLinkOut]
    total: int


class DomainCatalogOut(BaseModel):
    code: str
    label: str
    description: Optional[str] = None
    admin_route: Optional[str] = None
    sort_order: int
    is_active: bool
    regions: list[str] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class DomainCatalogListOut(BaseModel):
    items: list[DomainCatalogOut]
    total: int


class RoleCatalogOut(BaseModel):
    code: str
    label: str
    description: Optional[str] = None
    default_scope_type: str
    allowed_domains: list[str] = Field(default_factory=list)
    is_system: bool

    model_config = {"from_attributes": True}


class RoleCatalogListOut(BaseModel):
    items: list[RoleCatalogOut]
    total: int


class CrossDomainGrantCreateIn(BaseModel):
    user_id: str
    domain_code: str
    entity_type: str
    entity_id: str
    entity_label: Optional[str] = None
    permission_key: str
    scope_type: str = "ENTITY"
    expires_at: Optional[datetime] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CrossDomainGrantOut(BaseModel):
    id: str
    user_id: str
    domain_code: str
    entity_type: str
    entity_id: str
    entity_label: Optional[str] = None
    permission_key: str
    scope_type: str
    is_active: bool
    expires_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CrossDomainGrantListOut(BaseModel):
    items: list[CrossDomainGrantOut]
    total: int


class DomainHealthOut(BaseModel):
    domain: str
    label: str
    reachable: bool
    detail: Optional[str] = None
    admin_route: Optional[str] = None


class DomainHealthListOut(BaseModel):
    items: list[DomainHealthOut]
    reachable_count: int
    total: int


class EcosystemEntityOut(BaseModel):
    domain: str
    entity_type: str
    entity_id: str
    label: str
    source: str = "local"


class EcosystemMapOut(BaseModel):
    entities: list[EcosystemEntityOut]
    domains_probed: int
    remote_entities: int


class User360Out(BaseModel):
    user_id: str
    full_name: str
    email: str
    roles: list[str]
    permission_groups: list[str]
    domain_links: list[DomainLinkOut]
    cross_domain_grants: list[CrossDomainGrantOut]
    active_sessions: int
    remote_refs: list[EcosystemEntityOut] = Field(default_factory=list)


class SessionOut(BaseModel):
    id: str
    user_id: str
    auth_method: str
    identity_provider_code: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime
    expires_at: datetime
    revoked_at: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class SessionListOut(BaseModel):
    items: list[SessionOut]
    total: int


class WebhookDeliveryOut(BaseModel):
    id: str
    endpoint_id: str
    event_name: str
    status: str
    attempt_count: int
    last_status_code: Optional[int] = None
    created_at: datetime
    delivered_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class WebhookDeliveryListOut(BaseModel):
    items: list[WebhookDeliveryOut]
    total: int


class IdentityProviderOut(BaseModel):
    code: str
    name: str
    provider_type: str
    issuer_url: Optional[str] = None
    is_active: bool
    allowed_domains: list[str] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class IdentityProviderListOut(BaseModel):
    items: list[IdentityProviderOut]
    total: int


class PolicySnapshotCreateIn(BaseModel):
    version_label: str
    policy_kind: str = "RBAC"
    remark: Optional[str] = None
    created_by: Optional[str] = None


class PolicySnapshotOut(BaseModel):
    id: str
    version_label: str
    policy_kind: str
    remark: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime
    groups_count: int = 0
    permissions_count: int = 0

    model_config = {"from_attributes": True}


class PolicySnapshotListOut(BaseModel):
    items: list[PolicySnapshotOut]
    total: int


class LockerPlayerOut(BaseModel):
    player_code: str
    name: str
    segment: str
    parent_group: Optional[str] = None
    primary_domain: str
    integration_modes: list[str] = Field(default_factory=list)
    related_domains: list[str] = Field(default_factory=list)
    default_permissions: list[str] = Field(default_factory=list)
    regions: list[str] = Field(default_factory=list)
    global_tier: str
    ecosystem_player_id: Optional[str] = None
    locker_operator_ref: Optional[str] = None
    is_active: bool = True
    grants_count: int = 0
    user_access_count: int = 0

    model_config = {"from_attributes": True}


class LockerPlayerListOut(BaseModel):
    items: list[LockerPlayerOut]
    total: int
    priority_count: int = 0


class LockerPlayerSecurityProfileOut(BaseModel):
    player: LockerPlayerOut
    suggested_grants: list[CrossDomainGrantOut] = Field(default_factory=list)
    domain_links: list[DomainLinkOut] = Field(default_factory=list)
    ecosystem_match: Optional[dict[str, Any]] = None


class UserPlayerAccessCreateIn(BaseModel):
    user_id: str
    player_code: str
    access_role: str = "OPERATOR"
    scope_type: str = "NETWORK"
    granted_by: Optional[str] = None


class UserPlayerAccessOut(BaseModel):
    id: str
    user_id: str
    player_code: str
    access_role: str
    scope_type: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserPlayerAccessListOut(BaseModel):
    items: list[UserPlayerAccessOut]
    total: int


class PlayerSegmentOut(BaseModel):
    code: str
    label: str
    description: Optional[str] = None
    primary_domain: str
    sort_order: int
    icon_key: Optional[str] = None
    player_count: int = 0

    model_config = {"from_attributes": True}


class PlayerSegmentListOut(BaseModel):
    items: list[PlayerSegmentOut]
    total: int


class PlayerRelationOut(BaseModel):
    id: str
    from_player_code: str
    to_player_code: str
    relation_type: str
    strength: str
    notes: Optional[str] = None

    model_config = {"from_attributes": True}


class PlayerRelationListOut(BaseModel):
    items: list[PlayerRelationOut]
    total: int


class PlayerIntegrationOut(BaseModel):
    id: str
    player_code: str
    channel_type: str
    direction: str
    target_domain: str
    capability_key: str
    is_required: bool

    model_config = {"from_attributes": True}


class PlayerIntegrationListOut(BaseModel):
    items: list[PlayerIntegrationOut]
    total: int


class EcosystemTaxonomySummaryOut(BaseModel):
    total_players: int
    by_segment: dict[str, int]
    total_relations: int
    total_integrations: int
    food_delivery_players: list[str]
    collection_point_players: list[str]
    aggregator_players: list[str]
