-- USERS & ROLES & SECURITY — camada profissional / cross-domain mundial

CREATE TABLE IF NOT EXISTS security_domain_catalog (
    code character varying(32) NOT NULL PRIMARY KEY,
    label character varying(128) NOT NULL,
    description character varying(500),
    admin_route character varying(255),
    health_path character varying(255),
    sort_order integer DEFAULT 100 NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    regions_json text DEFAULT '[]',
    metadata_json text DEFAULT '{}',
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS security_role_catalog (
    code character varying(40) NOT NULL PRIMARY KEY,
    label character varying(128) NOT NULL,
    description character varying(500),
    default_scope_type character varying(40) DEFAULT 'GLOBAL',
    allowed_domains_json text DEFAULT '[]',
    is_system boolean DEFAULT true NOT NULL,
    sort_order integer DEFAULT 100 NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS security_cross_domain_grants (
    id character varying(36) NOT NULL PRIMARY KEY,
    user_id character varying(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    domain_code character varying(32) NOT NULL,
    entity_type character varying(48) NOT NULL,
    entity_id character varying(120) NOT NULL,
    entity_label character varying(255),
    permission_key character varying(80) NOT NULL,
    scope_type character varying(40) DEFAULT 'ENTITY' NOT NULL,
    granted_by character varying(36),
    expires_at timestamp with time zone,
    is_active boolean DEFAULT true NOT NULL,
    metadata_json text DEFAULT '{}',
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    UNIQUE (user_id, domain_code, entity_type, entity_id, permission_key)
);

CREATE TABLE IF NOT EXISTS security_user_sessions (
    id character varying(36) NOT NULL PRIMARY KEY,
    user_id character varying(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token_hash character varying(255) NOT NULL,
    user_agent character varying(500),
    ip_address character varying(64),
    auth_method character varying(32) DEFAULT 'API_KEY',
    identity_provider_code character varying(32),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    revoked_at timestamp with time zone,
    last_seen_at timestamp with time zone
);

CREATE TABLE IF NOT EXISTS security_webhook_deliveries (
    id character varying(36) NOT NULL PRIMARY KEY,
    endpoint_id character varying(36) NOT NULL REFERENCES security_webhook_endpoints(id) ON DELETE CASCADE,
    event_name character varying(100) NOT NULL,
    aggregate_type character varying(50),
    aggregate_id character varying(36),
    payload_json text NOT NULL,
    status character varying(20) DEFAULT 'PENDING' NOT NULL,
    attempt_count integer DEFAULT 0 NOT NULL,
    last_status_code integer,
    last_response_body text,
    next_attempt_at timestamp with time zone,
    delivered_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS security_identity_providers (
    code character varying(32) NOT NULL PRIMARY KEY,
    name character varying(128) NOT NULL,
    provider_type character varying(32) NOT NULL,
    issuer_url character varying(500),
    client_id_ref character varying(255),
    allowed_domains_json text DEFAULT '[]',
    is_active boolean DEFAULT true NOT NULL,
    metadata_json text DEFAULT '{}',
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS security_policy_snapshots (
    id character varying(36) NOT NULL PRIMARY KEY,
    version_label character varying(64) NOT NULL,
    policy_kind character varying(32) DEFAULT 'RBAC' NOT NULL,
    snapshot_json text NOT NULL,
    created_by character varying(36),
    remark text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_sec_grants_user_domain ON security_cross_domain_grants (user_id, domain_code);
CREATE INDEX IF NOT EXISTS ix_sec_sessions_user ON security_user_sessions (user_id, revoked_at);
CREATE INDEX IF NOT EXISTS ix_sec_wh_del_endpoint ON security_webhook_deliveries (endpoint_id, created_at DESC);
