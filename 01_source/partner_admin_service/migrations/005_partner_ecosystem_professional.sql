-- Camada profissional: capacidades, relações, presença por mercado

ALTER TABLE partner_ecosystem_players ADD COLUMN IF NOT EXISTS integration_status VARCHAR(16) DEFAULT 'PLANNED';
ALTER TABLE partner_ecosystem_players ADD COLUMN IF NOT EXISTS website_url VARCHAR(500);
ALTER TABLE partner_ecosystem_players ADD COLUMN IF NOT EXISTS estimated_locker_count INTEGER;
ALTER TABLE partner_ecosystem_players ADD COLUMN IF NOT EXISTS data_source VARCHAR(32) DEFAULT 'CATALOG';

CREATE TABLE IF NOT EXISTS partner_integration_capability_catalog (
    code VARCHAR(40) PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    category VARCHAR(32) NOT NULL DEFAULT 'CORE',
    default_protocol VARCHAR(20) NOT NULL DEFAULT 'REST',
    description TEXT,
    sort_order INTEGER NOT NULL DEFAULT 100
);

CREATE TABLE IF NOT EXISTS partner_player_capabilities (
    id VARCHAR(36) PRIMARY KEY,
    ecosystem_player_id VARCHAR(36) NOT NULL,
    capability_code VARCHAR(40) NOT NULL,
    protocol VARCHAR(20) NOT NULL DEFAULT 'REST',
    direction VARCHAR(10) NOT NULL DEFAULT 'OUTBOUND',
    enabled BOOLEAN NOT NULL DEFAULT 1,
    sandbox_ready BOOLEAN NOT NULL DEFAULT 0,
    production_ready BOOLEAN NOT NULL DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ecosystem_player_id) REFERENCES partner_ecosystem_players(id) ON DELETE CASCADE,
    FOREIGN KEY (capability_code) REFERENCES partner_integration_capability_catalog(code),
    UNIQUE (ecosystem_player_id, capability_code)
);

CREATE INDEX IF NOT EXISTS idx_partner_player_cap_player ON partner_player_capabilities(ecosystem_player_id);

CREATE TABLE IF NOT EXISTS partner_player_relations (
    id VARCHAR(36) PRIMARY KEY,
    from_player_id VARCHAR(36) NOT NULL,
    to_player_id VARCHAR(36) NOT NULL,
    relation_type VARCHAR(32) NOT NULL,
    strength VARCHAR(16) NOT NULL DEFAULT 'PRIMARY',
    notes TEXT,
    active BOOLEAN NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (from_player_id) REFERENCES partner_ecosystem_players(id) ON DELETE CASCADE,
    FOREIGN KEY (to_player_id) REFERENCES partner_ecosystem_players(id) ON DELETE CASCADE,
    UNIQUE (from_player_id, to_player_id, relation_type)
);

CREATE INDEX IF NOT EXISTS idx_partner_player_rel_from ON partner_player_relations(from_player_id, relation_type);

CREATE TABLE IF NOT EXISTS partner_market_presence (
    id VARCHAR(36) PRIMARY KEY,
    ecosystem_player_id VARCHAR(36) NOT NULL,
    country VARCHAR(2) NOT NULL,
    region_code VARCHAR(16),
    service_level VARCHAR(20) NOT NULL DEFAULT 'FULL',
    locker_density VARCHAR(16) NOT NULL DEFAULT 'MEDIUM',
    active BOOLEAN NOT NULL DEFAULT 1,
    launched_at DATE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ecosystem_player_id) REFERENCES partner_ecosystem_players(id) ON DELETE CASCADE,
    UNIQUE (ecosystem_player_id, country, region_code)
);

CREATE INDEX IF NOT EXISTS idx_partner_market_presence_country ON partner_market_presence(country, active);
