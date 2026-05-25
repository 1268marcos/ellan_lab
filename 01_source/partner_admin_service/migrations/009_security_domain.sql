-- USERS & ROLES & SECURITY (OPS) — alinhado a complete_schema_20260525_a.sql

CREATE TABLE IF NOT EXISTS security_permission_groups (
    id character varying(36) NOT NULL PRIMARY KEY,
    name character varying(255) NOT NULL UNIQUE,
    description character varying(500),
    is_system boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS security_permissions (
    id character varying(36) NOT NULL PRIMARY KEY,
    group_id character varying(36) NOT NULL REFERENCES security_permission_groups(id) ON DELETE CASCADE,
    object_key character varying(254) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    UNIQUE (group_id, object_key)
);

CREATE TABLE IF NOT EXISTS security_permission_memberships (
    id character varying(36) NOT NULL PRIMARY KEY,
    user_id character varying(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    group_id character varying(36) NOT NULL REFERENCES security_permission_groups(id) ON DELETE CASCADE,
    is_group_manager boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    UNIQUE (user_id, group_id)
);

CREATE TABLE IF NOT EXISTS security_webhook_endpoints (
    id character varying(36) NOT NULL PRIMARY KEY,
    owner_type character varying(20) NOT NULL DEFAULT 'PLATFORM',
    owner_id character varying(36),
    url character varying(500) NOT NULL,
    events_json text DEFAULT '["*"]' NOT NULL,
    secret_hash character varying(128) NOT NULL,
    secret_prefix character varying(16),
    signing_algo character varying(20) DEFAULT 'HMAC_SHA256' NOT NULL,
    active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS security_api_keys (
    id character varying(36) NOT NULL PRIMARY KEY,
    user_id character varying(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    key_prefix character varying(16) NOT NULL,
    key_hash character varying(128) NOT NULL,
    label character varying(64),
    scopes_json text DEFAULT '[]' NOT NULL,
    expires_at timestamp with time zone,
    last_used_at timestamp with time zone,
    revoked_at timestamp with time zone,
    created_by character varying(36),
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS security_audit_logs (
    id character varying(36) NOT NULL PRIMARY KEY,
    actor_id character varying(36),
    actor_role character varying(40),
    action character varying(80) NOT NULL,
    target_type character varying(40) NOT NULL,
    target_id character varying(36) NOT NULL,
    old_state_json text,
    new_state_json text,
    ip_address character varying(64),
    user_agent text,
    occurred_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS user_domain_links (
    id character varying(36) NOT NULL PRIMARY KEY,
    user_id character varying(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    domain character varying(32) NOT NULL,
    entity_type character varying(32) NOT NULL,
    entity_id character varying(36) NOT NULL,
    relation character varying(32) DEFAULT 'MEMBER' NOT NULL,
    is_primary boolean DEFAULT false NOT NULL,
    metadata_json text DEFAULT '{}',
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    UNIQUE (user_id, domain, entity_type, entity_id)
);

CREATE INDEX IF NOT EXISTS ix_sec_audit_actor_time ON security_audit_logs (actor_id, occurred_at DESC);
CREATE INDEX IF NOT EXISTS ix_sec_api_keys_user ON security_api_keys (user_id, revoked_at);
