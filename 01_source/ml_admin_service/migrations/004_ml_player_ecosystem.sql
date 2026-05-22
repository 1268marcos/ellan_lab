-- Ecossistema mundial de players locker/PUDO/marketplace/agregadores (nível profissional)

ALTER TABLE ml_locker_network_players ADD COLUMN IF NOT EXISTS global_tier VARCHAR(16) DEFAULT 'REGIONAL';
ALTER TABLE ml_locker_network_players ADD COLUMN IF NOT EXISTS integration_status VARCHAR(16) DEFAULT 'PLANNED';
ALTER TABLE ml_locker_network_players ADD COLUMN IF NOT EXISTS website_url VARCHAR(500);
ALTER TABLE ml_locker_network_players ADD COLUMN IF NOT EXISTS parent_player_id VARCHAR(36);
ALTER TABLE ml_locker_network_players ADD COLUMN IF NOT EXISTS estimated_locker_count INTEGER;
ALTER TABLE ml_locker_network_players ADD COLUMN IF NOT EXISTS data_source VARCHAR(32) DEFAULT 'CATALOG';

CREATE INDEX IF NOT EXISTS ix_ml_locker_network_tier ON ml_locker_network_players (global_tier, integration_status);

-- Catálogo de capacidades de integração (REST, webhook, OAuth…)
CREATE TABLE IF NOT EXISTS ml_integration_capability_catalog (
    code VARCHAR(40) NOT NULL PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    category VARCHAR(32) NOT NULL DEFAULT 'CORE',
    default_protocol VARCHAR(20) NOT NULL DEFAULT 'REST',
    description TEXT,
    sort_order INTEGER NOT NULL DEFAULT 100
);

-- Capacidades habilitadas por player
CREATE TABLE IF NOT EXISTS ml_player_capabilities (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    network_player_id VARCHAR(36) NOT NULL REFERENCES ml_locker_network_players(id) ON DELETE CASCADE,
    capability_code VARCHAR(40) NOT NULL REFERENCES ml_integration_capability_catalog(code),
    protocol VARCHAR(20) NOT NULL DEFAULT 'REST',
    direction VARCHAR(10) NOT NULL DEFAULT 'OUTBOUND',
    enabled BOOLEAN NOT NULL DEFAULT true,
    sandbox_ready BOOLEAN NOT NULL DEFAULT false,
    production_ready BOOLEAN NOT NULL DEFAULT false,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_ml_player_capability UNIQUE (network_player_id, capability_code)
);

CREATE INDEX IF NOT EXISTS ix_ml_player_cap_player ON ml_player_capabilities (network_player_id, enabled);

-- Relações entre players (agregador → carrier, marketplace → rede locker…)
CREATE TABLE IF NOT EXISTS ml_player_relations (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    from_player_id VARCHAR(36) NOT NULL REFERENCES ml_locker_network_players(id) ON DELETE CASCADE,
    to_player_id VARCHAR(36) NOT NULL REFERENCES ml_locker_network_players(id) ON DELETE CASCADE,
    relation_type VARCHAR(32) NOT NULL,
    strength VARCHAR(16) NOT NULL DEFAULT 'PRIMARY',
    notes TEXT,
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_ml_player_relation UNIQUE (from_player_id, to_player_id, relation_type),
    CONSTRAINT chk_ml_player_relation_diff CHECK (from_player_id <> to_player_id)
);

CREATE INDEX IF NOT EXISTS ix_ml_player_rel_from ON ml_player_relations (from_player_id, relation_type);
CREATE INDEX IF NOT EXISTS ix_ml_player_rel_to ON ml_player_relations (to_player_id);

-- Presença por mercado (país/região)
CREATE TABLE IF NOT EXISTS ml_market_presence (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    network_player_id VARCHAR(36) NOT NULL REFERENCES ml_locker_network_players(id) ON DELETE CASCADE,
    country VARCHAR(2) NOT NULL,
    region_code VARCHAR(16),
    service_level VARCHAR(20) NOT NULL DEFAULT 'FULL',
    locker_density VARCHAR(16) NOT NULL DEFAULT 'MEDIUM',
    active BOOLEAN NOT NULL DEFAULT true,
    launched_at DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_ml_market_presence UNIQUE (network_player_id, country, region_code)
);

CREATE INDEX IF NOT EXISTS ix_ml_market_presence_country ON ml_market_presence (country, active);
