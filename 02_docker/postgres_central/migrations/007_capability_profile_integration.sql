-- Perfil capability: webhook + API key (admin OPS)
CREATE TABLE IF NOT EXISTS capability_profile_webhook (
    id VARCHAR(36) PRIMARY KEY,
    profile_id BIGINT NOT NULL REFERENCES capability_profile(id) ON DELETE CASCADE,
    profile_code VARCHAR(160) NOT NULL,
    url VARCHAR(500) NOT NULL,
    secret_hash VARCHAR(128) NOT NULL,
    secret_preview VARCHAR(32),
    event_types_json TEXT NOT NULL DEFAULT '["capability.profile.changed"]',
    active BOOLEAN NOT NULL DEFAULT TRUE,
    last_http_status INTEGER,
    last_delivered_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_capability_profile_webhook_profile UNIQUE (profile_id)
);

CREATE INDEX IF NOT EXISTS ix_cap_profile_webhook_code ON capability_profile_webhook(profile_code);

CREATE TABLE IF NOT EXISTS capability_profile_api_key (
    id VARCHAR(36) PRIMARY KEY,
    profile_id BIGINT NOT NULL REFERENCES capability_profile(id) ON DELETE CASCADE,
    profile_code VARCHAR(160) NOT NULL,
    key_prefix VARCHAR(16) NOT NULL,
    key_hash VARCHAR(128) NOT NULL,
    label VARCHAR(120),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    rotated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_cap_profile_api_key_profile ON capability_profile_api_key(profile_id, active);
