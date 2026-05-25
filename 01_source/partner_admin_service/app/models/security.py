from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, Numeric, String, Text

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SecurityPermissionGroup(Base):
    __tablename__ = "security_permission_groups"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(String(500), nullable=True)
    is_system = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class SecurityPermission(Base):
    __tablename__ = "security_permissions"

    id = Column(String(36), primary_key=True)
    group_id = Column(String(36), nullable=False, index=True)
    object_key = Column(String(254), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class SecurityPermissionMembership(Base):
    __tablename__ = "security_permission_memberships"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), nullable=False, index=True)
    group_id = Column(String(36), nullable=False, index=True)
    is_group_manager = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class SecurityWebhookEndpoint(Base):
    __tablename__ = "security_webhook_endpoints"

    id = Column(String(36), primary_key=True)
    owner_type = Column(String(20), nullable=False, default="PLATFORM")
    owner_id = Column(String(36), nullable=True)
    url = Column(String(500), nullable=False)
    events_json = Column(Text, nullable=False, default='["*"]')
    secret_hash = Column(String(128), nullable=False)
    secret_prefix = Column(String(16), nullable=True)
    signing_algo = Column(String(20), nullable=False, default="HMAC_SHA256")
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class SecurityApiKey(Base):
    __tablename__ = "security_api_keys"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), nullable=False, index=True)
    key_prefix = Column(String(16), nullable=False)
    key_hash = Column(String(128), nullable=False)
    label = Column(String(64), nullable=True)
    scopes_json = Column(Text, nullable=False, default="[]")
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(String(36), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class SecurityAuditLog(Base):
    __tablename__ = "security_audit_logs"

    id = Column(String(36), primary_key=True)
    actor_id = Column(String(36), nullable=True, index=True)
    actor_role = Column(String(40), nullable=True)
    action = Column(String(80), nullable=False)
    target_type = Column(String(40), nullable=False)
    target_id = Column(String(36), nullable=False)
    old_state_json = Column(Text, nullable=True)
    new_state_json = Column(Text, nullable=True)
    ip_address = Column(String(64), nullable=True)
    user_agent = Column(Text, nullable=True)
    occurred_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class UserDomainLink(Base):
    __tablename__ = "user_domain_links"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), nullable=False, index=True)
    domain = Column(String(32), nullable=False)
    entity_type = Column(String(32), nullable=False)
    entity_id = Column(String(36), nullable=False)
    relation = Column(String(32), nullable=False, default="MEMBER")
    is_primary = Column(Boolean, nullable=False, default=False)
    metadata_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class SecurityDomainCatalog(Base):
    __tablename__ = "security_domain_catalog"

    code = Column(String(32), primary_key=True)
    label = Column(String(128), nullable=False)
    description = Column(String(500), nullable=True)
    admin_route = Column(String(255), nullable=True)
    health_path = Column(String(255), nullable=True)
    sort_order = Column(Integer, nullable=False, default=100)
    is_active = Column(Boolean, nullable=False, default=True)
    regions_json = Column(Text, nullable=False, default="[]")
    metadata_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class SecurityRoleCatalog(Base):
    __tablename__ = "security_role_catalog"

    code = Column(String(40), primary_key=True)
    label = Column(String(128), nullable=False)
    description = Column(String(500), nullable=True)
    default_scope_type = Column(String(40), nullable=False, default="GLOBAL")
    allowed_domains_json = Column(Text, nullable=False, default="[]")
    is_system = Column(Boolean, nullable=False, default=True)
    sort_order = Column(Integer, nullable=False, default=100)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class SecurityCrossDomainGrant(Base):
    __tablename__ = "security_cross_domain_grants"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), nullable=False, index=True)
    domain_code = Column(String(32), nullable=False, index=True)
    entity_type = Column(String(48), nullable=False)
    entity_id = Column(String(120), nullable=False)
    entity_label = Column(String(255), nullable=True)
    permission_key = Column(String(80), nullable=False)
    scope_type = Column(String(40), nullable=False, default="ENTITY")
    granted_by = Column(String(36), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    metadata_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class SecurityUserSession(Base):
    __tablename__ = "security_user_sessions"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), nullable=False, index=True)
    session_token_hash = Column(String(255), nullable=False)
    user_agent = Column(String(500), nullable=True)
    ip_address = Column(String(64), nullable=True)
    auth_method = Column(String(32), nullable=False, default="API_KEY")
    identity_provider_code = Column(String(32), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    last_seen_at = Column(DateTime(timezone=True), nullable=True)


class SecurityWebhookDelivery(Base):
    __tablename__ = "security_webhook_deliveries"

    id = Column(String(36), primary_key=True)
    endpoint_id = Column(String(36), nullable=False, index=True)
    event_name = Column(String(100), nullable=False)
    aggregate_type = Column(String(50), nullable=True)
    aggregate_id = Column(String(36), nullable=True)
    payload_json = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="PENDING")
    attempt_count = Column(Integer, nullable=False, default=0)
    last_status_code = Column(Integer, nullable=True)
    last_response_body = Column(Text, nullable=True)
    next_attempt_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class SecurityIdentityProvider(Base):
    __tablename__ = "security_identity_providers"

    code = Column(String(32), primary_key=True)
    name = Column(String(128), nullable=False)
    provider_type = Column(String(32), nullable=False)
    issuer_url = Column(String(500), nullable=True)
    client_id_ref = Column(String(255), nullable=True)
    allowed_domains_json = Column(Text, nullable=False, default="[]")
    is_active = Column(Boolean, nullable=False, default=True)
    metadata_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class SecurityPolicySnapshot(Base):
    __tablename__ = "security_policy_snapshots"

    id = Column(String(36), primary_key=True)
    version_label = Column(String(64), nullable=False)
    policy_kind = Column(String(32), nullable=False, default="RBAC")
    snapshot_json = Column(Text, nullable=False)
    created_by = Column(String(36), nullable=True)
    remark = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class SecurityLockerPlayerRegistry(Base):
    __tablename__ = "security_locker_player_registry"

    player_code = Column(String(48), primary_key=True)
    name = Column(String(160), nullable=False)
    segment = Column(String(32), nullable=False)
    parent_group = Column(String(40), nullable=True)
    primary_domain = Column(String(32), nullable=False)
    integration_modes_json = Column(Text, nullable=False, default="[]")
    external_refs_json = Column(Text, nullable=False, default="{}")
    related_domains_json = Column(Text, nullable=False, default="[]")
    default_permission_keys_json = Column(Text, nullable=False, default="[]")
    regions_json = Column(Text, nullable=False, default="[]")
    global_tier = Column(String(20), nullable=False, default="REGIONAL")
    ecosystem_player_id = Column(String(36), nullable=True)
    locker_operator_ref = Column(String(48), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    metadata_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class SecurityPlayerSegment(Base):
    __tablename__ = "security_player_segments"

    code = Column(String(32), primary_key=True)
    label = Column(String(128), nullable=False)
    description = Column(String(500), nullable=True)
    primary_domain = Column(String(32), nullable=False)
    sort_order = Column(Integer, nullable=False, default=100)
    icon_key = Column(String(32), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)


class SecurityPlayerRelation(Base):
    __tablename__ = "security_player_relations"

    id = Column(String(36), primary_key=True)
    from_player_code = Column(String(48), nullable=False, index=True)
    to_player_code = Column(String(48), nullable=False, index=True)
    relation_type = Column(String(40), nullable=False)
    strength = Column(String(16), nullable=False, default="PRIMARY")
    notes = Column(String(500), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class SecurityPlayerIntegration(Base):
    __tablename__ = "security_player_integrations"

    id = Column(String(36), primary_key=True)
    player_code = Column(String(48), nullable=False, index=True)
    channel_type = Column(String(32), nullable=False)
    direction = Column(String(16), nullable=False, default="BIDIRECTIONAL")
    target_domain = Column(String(32), nullable=False)
    capability_key = Column(String(64), nullable=False)
    is_required = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    metadata_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class SecurityUserPlayerAccess(Base):
    __tablename__ = "security_user_player_access"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), nullable=False, index=True)
    player_code = Column(String(48), nullable=False, index=True)
    access_role = Column(String(40), nullable=False)
    scope_type = Column(String(40), nullable=False, default="NETWORK")
    granted_by = Column(String(36), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class SecurityRoleTemplate(Base):
    __tablename__ = "security_role_templates"

    id = Column(String(36), primary_key=True)
    code = Column(String(48), nullable=False, unique=True)
    name = Column(String(128), nullable=False)
    description = Column(String(500), nullable=True)
    roles_json = Column(Text, nullable=False, default="[]")
    permission_groups_json = Column(Text, nullable=False, default="[]")
    default_players_json = Column(Text, nullable=False, default="[]")
    target_segment = Column(String(32), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class SecurityRiskScore(Base):
    __tablename__ = "security_risk_scores"

    id = Column(String(36), primary_key=True)
    entity_type = Column(String(32), nullable=False)
    entity_id = Column(String(120), nullable=False, index=True)
    score = Column(Numeric(5, 2), nullable=False)
    risk_tier = Column(String(16), nullable=False)
    factors_json = Column(Text, nullable=False, default="[]")
    computed_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    expires_at = Column(DateTime(timezone=True), nullable=True)


class SecurityAccessReviewCampaign(Base):
    __tablename__ = "security_access_review_campaigns"

    id = Column(String(36), primary_key=True)
    name = Column(String(128), nullable=False)
    status = Column(String(20), nullable=False, default="DRAFT")
    due_at = Column(DateTime(timezone=True), nullable=False)
    scope_json = Column(Text, nullable=False, default="{}")
    created_by = Column(String(36), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class SecurityAccessReviewItem(Base):
    __tablename__ = "security_access_review_items"

    id = Column(String(36), primary_key=True)
    campaign_id = Column(String(36), nullable=False, index=True)
    user_id = Column(String(36), nullable=False, index=True)
    subject_type = Column(String(32), nullable=False)
    subject_id = Column(String(120), nullable=False)
    subject_label = Column(String(255), nullable=True)
    decision = Column(String(20), nullable=True)
    reviewer_id = Column(String(36), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class SecurityBreakGlassEvent(Base):
    __tablename__ = "security_break_glass_events"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), nullable=False, index=True)
    reason = Column(String(500), nullable=False)
    granted_roles_json = Column(Text, nullable=False, default="[]")
    approved_by = Column(String(36), nullable=True)
    status = Column(String(20), nullable=False, default="ACTIVE")
    started_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    audit_ref = Column(String(36), nullable=True)


class SecurityAlertRule(Base):
    __tablename__ = "security_alert_rules"

    id = Column(String(36), primary_key=True)
    code = Column(String(48), nullable=False, unique=True)
    name = Column(String(128), nullable=False)
    condition_type = Column(String(40), nullable=False)
    threshold_json = Column(Text, nullable=False, default="{}")
    severity = Column(String(16), nullable=False, default="MEDIUM")
    notify_channels_json = Column(Text, nullable=False, default='["OPS_CONSOLE"]')
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class SecurityAlert(Base):
    __tablename__ = "security_alerts"

    id = Column(String(36), primary_key=True)
    rule_id = Column(String(36), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    detail = Column(Text, nullable=True)
    entity_type = Column(String(32), nullable=True)
    entity_id = Column(String(120), nullable=True)
    severity = Column(String(16), nullable=False)
    status = Column(String(20), nullable=False, default="OPEN")
    acknowledged_by = Column(String(36), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class SecurityComplianceControl(Base):
    __tablename__ = "security_compliance_controls"

    code = Column(String(48), primary_key=True)
    framework = Column(String(32), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    domain = Column(String(32), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)


class SecurityControlMapping(Base):
    __tablename__ = "security_control_mappings"

    id = Column(String(36), primary_key=True)
    control_code = Column(String(48), nullable=False, index=True)
    object_key = Column(String(254), nullable=False)
    coverage_level = Column(String(16), nullable=False, default="PARTIAL")
