-- Registro mundial locker/PUDO/marketplace ↔ segurança cross-domain

CREATE TABLE IF NOT EXISTS security_locker_player_registry (
    player_code character varying(48) NOT NULL PRIMARY KEY,
    name character varying(160) NOT NULL,
    segment character varying(32) NOT NULL,
    primary_domain character varying(32) NOT NULL,
    related_domains_json text DEFAULT '[]' NOT NULL,
    default_permission_keys_json text DEFAULT '[]' NOT NULL,
    regions_json text DEFAULT '[]' NOT NULL,
    global_tier character varying(20) DEFAULT 'REGIONAL' NOT NULL,
    ecosystem_player_id character varying(36),
    locker_operator_ref character varying(48),
    is_active boolean DEFAULT true NOT NULL,
    metadata_json text DEFAULT '{}',
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS security_user_player_access (
    id character varying(36) NOT NULL PRIMARY KEY,
    user_id character varying(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    player_code character varying(48) NOT NULL REFERENCES security_locker_player_registry(player_code) ON DELETE CASCADE,
    access_role character varying(40) NOT NULL,
    scope_type character varying(40) DEFAULT 'NETWORK' NOT NULL,
    granted_by character varying(36),
    is_active boolean DEFAULT true NOT NULL,
    expires_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    UNIQUE (user_id, player_code, access_role)
);

CREATE INDEX IF NOT EXISTS ix_sec_user_player_user ON security_user_player_access (user_id, is_active);
CREATE INDEX IF NOT EXISTS ix_sec_locker_player_tier ON security_locker_player_registry (global_tier, segment);
