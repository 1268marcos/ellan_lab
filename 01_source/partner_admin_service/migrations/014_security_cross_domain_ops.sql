-- Pedidos de acesso, JIT grants, delegação act-as, cache de entitlements remotos

CREATE TABLE IF NOT EXISTS security_access_requests (
    id character varying(36) NOT NULL PRIMARY KEY,
    requester_id character varying(36) NOT NULL,
    user_id character varying(36) NOT NULL,
    domain_code character varying(32) NOT NULL,
    entity_type character varying(48) NOT NULL,
    entity_id character varying(120) NOT NULL,
    entity_label character varying(255),
    permission_key character varying(80) NOT NULL,
    justification character varying(500) NOT NULL,
    status character varying(20) DEFAULT 'PENDING' NOT NULL,
    reviewer_id character varying(36),
    reviewed_at timestamp with time zone,
    review_notes text,
    grant_id character varying(36),
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS security_jit_grants (
    id character varying(36) NOT NULL PRIMARY KEY,
    user_id character varying(36) NOT NULL,
    domain_code character varying(32) NOT NULL,
    entity_type character varying(48) NOT NULL,
    entity_id character varying(120) NOT NULL,
    permission_key character varying(80) NOT NULL,
    grant_id character varying(36),
    reason character varying(500) NOT NULL,
    approved_by character varying(36),
    status character varying(20) DEFAULT 'ACTIVE' NOT NULL,
    started_at timestamp with time zone DEFAULT now() NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    revoked_at timestamp with time zone
);

CREATE TABLE IF NOT EXISTS security_delegation_sessions (
    id character varying(36) NOT NULL PRIMARY KEY,
    delegate_user_id character varying(36) NOT NULL,
    target_domain character varying(32) NOT NULL,
    target_entity_type character varying(48) NOT NULL,
    target_entity_id character varying(120) NOT NULL,
    target_entity_label character varying(255),
    reason character varying(500) NOT NULL,
    approved_by character varying(36),
    status character varying(20) DEFAULT 'ACTIVE' NOT NULL,
    started_at timestamp with time zone DEFAULT now() NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    ended_at timestamp with time zone
);

CREATE TABLE IF NOT EXISTS security_domain_entitlements (
    id character varying(36) NOT NULL PRIMARY KEY,
    domain_code character varying(32) NOT NULL,
    remote_entity_type character varying(48) NOT NULL,
    remote_entity_id character varying(120) NOT NULL,
    remote_label character varying(255),
    entitlement_key character varying(80) NOT NULL,
    source_service character varying(64) NOT NULL,
    synced_at timestamp with time zone DEFAULT now() NOT NULL,
    metadata_json text DEFAULT '{}' NOT NULL,
    UNIQUE (domain_code, remote_entity_type, remote_entity_id, entitlement_key)
);

CREATE INDEX IF NOT EXISTS ix_sec_access_req_status ON security_access_requests (status, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_sec_jit_grants_user ON security_jit_grants (user_id, status, expires_at);
CREATE INDEX IF NOT EXISTS ix_sec_delegation_active ON security_delegation_sessions (delegate_user_id, status);
