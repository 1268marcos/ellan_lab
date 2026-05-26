-- Integração mundial: perfis API + capabilities por player (BI / Analytics / ML)

CREATE TABLE IF NOT EXISTS bi_player_integration_profiles (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    network_player_code VARCHAR(48) NOT NULL,
    segment_code VARCHAR(32) NOT NULL,
    integration_mode VARCHAR(32) NOT NULL DEFAULT 'API',
    api_base_url VARCHAR(500),
    auth_method VARCHAR(32) NOT NULL DEFAULT 'API_KEY',
    webhook_support BOOLEAN NOT NULL DEFAULT false,
    bi_data_feed BOOLEAN NOT NULL DEFAULT true,
    ml_scoring_enabled BOOLEAN NOT NULL DEFAULT false,
    target_service VARCHAR(48) NOT NULL DEFAULT 'analytics-bi-admin',
    docs_url VARCHAR(500),
    status VARCHAR(20) NOT NULL DEFAULT 'PLANNED',
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_bi_integration_player UNIQUE (network_player_code)
);

CREATE INDEX IF NOT EXISTS ix_bi_integration_segment ON bi_player_integration_profiles (segment_code, status);

CREATE TABLE IF NOT EXISTS bi_player_capability_links (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    network_player_code VARCHAR(48) NOT NULL,
    capability_code VARCHAR(40) NOT NULL,
    capability_name VARCHAR(120),
    protocol VARCHAR(16) NOT NULL DEFAULT 'REST',
    direction VARCHAR(16) NOT NULL DEFAULT 'OUTBOUND',
    production_ready BOOLEAN NOT NULL DEFAULT false,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_bi_cap_player_code UNIQUE (network_player_code, capability_code)
);

CREATE INDEX IF NOT EXISTS ix_bi_cap_player ON bi_player_capability_links (network_player_code);

CREATE TABLE IF NOT EXISTS bi_cross_domain_integrations (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    source_player_code VARCHAR(48) NOT NULL,
    target_domain VARCHAR(24) NOT NULL,
    target_player_code VARCHAR(48),
    integration_type VARCHAR(32) NOT NULL DEFAULT 'DATA_SYNC',
    route_path VARCHAR(255),
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_bi_cross_domain_source ON bi_cross_domain_integrations (source_player_code, target_domain);
