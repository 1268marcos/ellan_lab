-- Camada Global OPS: certificações, corredores, prontidão por player, saúde em cascata

CREATE TABLE IF NOT EXISTS partner_player_certifications (
    id VARCHAR(36) PRIMARY KEY,
    ecosystem_player_id VARCHAR(36) NOT NULL,
    player_code VARCHAR(48) NOT NULL,
    certification_type VARCHAR(40) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'VALID',
    issuer VARCHAR(120),
    issued_at DATE,
    expires_at DATE,
    evidence_url VARCHAR(500),
    scope_notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ecosystem_player_id) REFERENCES partner_ecosystem_players(id) ON DELETE CASCADE,
    UNIQUE (ecosystem_player_id, certification_type)
);

CREATE INDEX IF NOT EXISTS ix_partner_cert_player ON partner_player_certifications(player_code, status);

CREATE TABLE IF NOT EXISTS partner_global_corridors (
    id VARCHAR(36) PRIMARY KEY,
    corridor_code VARCHAR(48) NOT NULL UNIQUE,
    name VARCHAR(160) NOT NULL,
    origin_country VARCHAR(2) NOT NULL,
    dest_country VARCHAR(2) NOT NULL,
    primary_player_id VARCHAR(36) NOT NULL,
    primary_player_code VARCHAR(48) NOT NULL,
    fallback_player_id VARCHAR(36),
    fallback_player_code VARCHAR(48),
    handoff_type VARCHAR(32) NOT NULL DEFAULT 'LOCKER_TO_LOCKER',
    service_level VARCHAR(20) NOT NULL DEFAULT 'STANDARD',
    transit_days_min INTEGER NOT NULL DEFAULT 1,
    transit_days_max INTEGER NOT NULL DEFAULT 5,
    supports_returns BOOLEAN NOT NULL DEFAULT 0,
    active BOOLEAN NOT NULL DEFAULT 1,
    priority INTEGER NOT NULL DEFAULT 100,
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (primary_player_id) REFERENCES partner_ecosystem_players(id),
    FOREIGN KEY (fallback_player_id) REFERENCES partner_ecosystem_players(id)
);

CREATE INDEX IF NOT EXISTS ix_partner_corridor_route ON partner_global_corridors(origin_country, dest_country, active);

CREATE TABLE IF NOT EXISTS partner_ecosystem_readiness (
    ecosystem_player_id VARCHAR(36) PRIMARY KEY,
    player_code VARCHAR(48) NOT NULL UNIQUE,
    score_total NUMERIC(5, 2) NOT NULL DEFAULT 0,
    score_certifications NUMERIC(5, 2) NOT NULL DEFAULT 0,
    score_capabilities NUMERIC(5, 2) NOT NULL DEFAULT 0,
    score_corridors NUMERIC(5, 2) NOT NULL DEFAULT 0,
    score_webhooks NUMERIC(5, 2) NOT NULL DEFAULT 0,
    readiness_band VARCHAR(16) NOT NULL DEFAULT 'PLANNED',
    blockers_json TEXT NOT NULL DEFAULT '[]',
    computed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_partner_eco_readiness_band ON partner_ecosystem_readiness(readiness_band, score_total DESC);

CREATE TABLE IF NOT EXISTS partner_relation_health (
    id VARCHAR(36) PRIMARY KEY,
    relation_id VARCHAR(36) NOT NULL UNIQUE,
    from_player_code VARCHAR(48) NOT NULL,
    to_player_code VARCHAR(48) NOT NULL,
    relation_type VARCHAR(32) NOT NULL,
    health_status VARCHAR(20) NOT NULL DEFAULT 'HEALTHY',
    cascade_from_player_code VARCHAR(48),
    last_check_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    details_json TEXT NOT NULL DEFAULT '{}',
    FOREIGN KEY (relation_id) REFERENCES partner_player_relations(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_partner_rel_health_status ON partner_relation_health(health_status, last_check_at DESC);
