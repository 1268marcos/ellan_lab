-- Catálogo global de players locker/PUDO/marketplace + vínculos com partners OPS

CREATE TABLE IF NOT EXISTS partner_ecosystem_players (
    id VARCHAR(36) PRIMARY KEY,
    code VARCHAR(48) NOT NULL UNIQUE,
    name VARCHAR(160) NOT NULL,
    player_role VARCHAR(40) NOT NULL,
    parent_group VARCHAR(40) NOT NULL,
    country VARCHAR(2) NOT NULL,
    regions_json TEXT NOT NULL DEFAULT '[]',
    supports_lockers BOOLEAN NOT NULL DEFAULT 0,
    supports_marketplace BOOLEAN NOT NULL DEFAULT 0,
    integration_mode VARCHAR(40) NOT NULL DEFAULT 'DIRECT_API',
    marketplace_channel_id VARCHAR(36),
    marketplace_channel_code VARCHAR(48),
    locker_operator_ref VARCHAR(48),
    ecommerce_partner_code VARCHAR(48),
    api_docs_url VARCHAR(500),
    notes TEXT,
    global_tier VARCHAR(20) NOT NULL DEFAULT 'REGIONAL',
    sort_order INTEGER NOT NULL DEFAULT 100,
    active BOOLEAN NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_partner_ecosystem_parent ON partner_ecosystem_players(parent_group);
CREATE INDEX IF NOT EXISTS idx_partner_ecosystem_tier ON partner_ecosystem_players(global_tier);

CREATE TABLE IF NOT EXISTS partner_ecosystem_links (
    id VARCHAR(36) PRIMARY KEY,
    partner_id VARCHAR(36) NOT NULL,
    partner_type VARCHAR(20) NOT NULL,
    ecosystem_player_id VARCHAR(36) NOT NULL,
    link_role VARCHAR(40) NOT NULL DEFAULT 'CHANNEL',
    is_primary BOOLEAN NOT NULL DEFAULT 0,
    integration_status VARCHAR(30) NOT NULL DEFAULT 'PLANNED',
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ecosystem_player_id) REFERENCES partner_ecosystem_players(id)
);

CREATE INDEX IF NOT EXISTS idx_partner_ecosystem_links_partner ON partner_ecosystem_links(partner_id, partner_type);
CREATE UNIQUE INDEX IF NOT EXISTS uq_partner_ecosystem_link ON partner_ecosystem_links(partner_id, partner_type, ecosystem_player_id);
