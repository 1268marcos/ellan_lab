-- capability ecosystem global (integration modes, player integrations, relations)
-- Source: 01_source/capability_admin_service/migrations/003_capability_ecosystem_global.sql

CREATE TABLE IF NOT EXISTS capability_integration_mode (
    id BIGSERIAL PRIMARY KEY,
    code VARCHAR(40) NOT NULL UNIQUE,
    name VARCHAR(120) NOT NULL,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS capability_player_integration (
    id BIGSERIAL PRIMARY KEY,
    player_id BIGINT NOT NULL REFERENCES capability_ecosystem_player(id) ON DELETE CASCADE,
    player_code VARCHAR(48) NOT NULL,
    integration_mode_code VARCHAR(40) NOT NULL REFERENCES capability_integration_mode(code),
    direction VARCHAR(10) NOT NULL DEFAULT 'OUTBOUND',
    auth_type VARCHAR(32) NOT NULL DEFAULT 'API_KEY',
    base_url_template VARCHAR(500),
    webhook_supported BOOLEAN NOT NULL DEFAULT FALSE,
    sandbox_available BOOLEAN NOT NULL DEFAULT TRUE,
    production_ready BOOLEAN NOT NULL DEFAULT FALSE,
    metadata_json JSONB NOT NULL DEFAULT '{}',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_capability_player_integration UNIQUE (player_id, integration_mode_code, direction)
);

CREATE INDEX IF NOT EXISTS ix_cap_player_integration_code ON capability_player_integration(player_code);

CREATE TABLE IF NOT EXISTS capability_player_relation (
    id BIGSERIAL PRIMARY KEY,
    from_player_id BIGINT NOT NULL REFERENCES capability_ecosystem_player(id) ON DELETE CASCADE,
    to_player_id BIGINT NOT NULL REFERENCES capability_ecosystem_player(id) ON DELETE CASCADE,
    from_player_code VARCHAR(48) NOT NULL,
    to_player_code VARCHAR(48) NOT NULL,
    relation_type VARCHAR(32) NOT NULL,
    notes TEXT,
    metadata_json JSONB NOT NULL DEFAULT '{}',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_capability_player_relation UNIQUE (from_player_id, to_player_id, relation_type)
);

CREATE INDEX IF NOT EXISTS ix_cap_player_relation_from ON capability_player_relation(from_player_code);
