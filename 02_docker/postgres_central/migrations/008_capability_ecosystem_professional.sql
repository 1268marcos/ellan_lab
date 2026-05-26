-- capability admin prompt 2: ecossistema + auditoria + DLQ
CREATE TABLE IF NOT EXISTS capability_ecosystem_segment (
    id BIGSERIAL PRIMARY KEY,
    code VARCHAR(40) NOT NULL UNIQUE,
    name VARCHAR(120) NOT NULL,
    description TEXT,
    sort_order INTEGER NOT NULL DEFAULT 100,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS capability_ecosystem_player (
    id BIGSERIAL PRIMARY KEY,
    code VARCHAR(48) NOT NULL,
    name VARCHAR(160) NOT NULL,
    segment_id BIGINT NOT NULL REFERENCES capability_ecosystem_segment(id) ON DELETE RESTRICT,
    country_codes VARCHAR(120) NOT NULL DEFAULT '*',
    headquarters_country CHAR(2),
    integration_protocol VARCHAR(20) NOT NULL DEFAULT 'REST',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    metadata_json JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_capability_ecosystem_player_code UNIQUE (code)
);

CREATE TABLE IF NOT EXISTS capability_profile_player_binding (
    id BIGSERIAL PRIMARY KEY,
    profile_id BIGINT NOT NULL REFERENCES capability_profile(id) ON DELETE CASCADE,
    player_id BIGINT NOT NULL REFERENCES capability_ecosystem_player(id) ON DELETE CASCADE,
    profile_code VARCHAR(160) NOT NULL,
    player_code VARCHAR(48) NOT NULL,
    binding_role VARCHAR(32) NOT NULL DEFAULT 'PRIMARY',
    priority INTEGER NOT NULL DEFAULT 100,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    metadata_json JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_capability_profile_player_binding UNIQUE (profile_id, player_id)
);

CREATE TABLE IF NOT EXISTS capability_profile_audit_log (
    id VARCHAR(36) PRIMARY KEY,
    profile_id BIGINT REFERENCES capability_profile(id) ON DELETE SET NULL,
    entity_type VARCHAR(48) NOT NULL,
    entity_id VARCHAR(64) NOT NULL,
    action VARCHAR(32) NOT NULL,
    actor VARCHAR(120),
    payload_json JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS capability_profile_webhook_delivery (
    id VARCHAR(36) PRIMARY KEY,
    webhook_id VARCHAR(36) NOT NULL REFERENCES capability_profile_webhook(id) ON DELETE CASCADE,
    event_type VARCHAR(48) NOT NULL,
    payload_json TEXT NOT NULL,
    http_status INTEGER,
    success BOOLEAN NOT NULL DEFAULT FALSE,
    status VARCHAR(20) NOT NULL DEFAULT 'DELIVERED',
    attempt_count INTEGER NOT NULL DEFAULT 1,
    dead_lettered_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
