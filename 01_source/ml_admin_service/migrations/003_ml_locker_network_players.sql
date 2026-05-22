-- Redes locker mundiais para ML (InPost, DHL, Magalu, Mercado Livre, Amazon, DPD, Correios, CTT…)

ALTER TABLE ml_data_partners ADD COLUMN IF NOT EXISTS network_player_code VARCHAR(48);
CREATE INDEX IF NOT EXISTS ix_ml_data_partners_network ON ml_data_partners (network_player_code);

CREATE TABLE IF NOT EXISTS ml_locker_network_players (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    code VARCHAR(48) NOT NULL UNIQUE,
    name VARCHAR(140) NOT NULL,
    player_role VARCHAR(40) NOT NULL,
    parent_group VARCHAR(32) NOT NULL DEFAULT 'LOCKER_NETWORK',
    country VARCHAR(2) NOT NULL,
    regions_json TEXT NOT NULL DEFAULT '[]',
    supports_lockers BOOLEAN NOT NULL DEFAULT true,
    supports_marketplace BOOLEAN NOT NULL DEFAULT false,
    integration_mode VARCHAR(32) NOT NULL DEFAULT 'DIRECT_API',
    marketplace_channel_id VARCHAR(36),
    marketplace_channel_code VARCHAR(48),
    locker_operator_ref VARCHAR(64),
    ecommerce_partner_code VARCHAR(32),
    api_docs_url VARCHAR(500),
    ml_scoring_weight NUMERIC(4, 2) NOT NULL DEFAULT 1.00,
    ml_notes TEXT,
    sort_order INTEGER NOT NULL DEFAULT 100,
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_ml_locker_network_parent ON ml_locker_network_players (parent_group, active);
CREATE INDEX IF NOT EXISTS ix_ml_locker_network_country ON ml_locker_network_players (country);

CREATE TABLE IF NOT EXISTS ml_network_ml_profiles (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    network_player_id VARCHAR(36) NOT NULL REFERENCES ml_locker_network_players(id) ON DELETE CASCADE,
    use_case_id VARCHAR(36) REFERENCES ml_use_cases(id) ON DELETE SET NULL,
    telemetry_density VARCHAR(16) NOT NULL DEFAULT 'MEDIUM',
    drift_baseline_psi NUMERIC(6, 4) DEFAULT 0.10,
    feature_pack_json TEXT NOT NULL DEFAULT '[]',
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_ml_network_profile UNIQUE (network_player_id, use_case_id)
);
