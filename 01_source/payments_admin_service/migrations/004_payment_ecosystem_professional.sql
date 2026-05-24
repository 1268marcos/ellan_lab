-- Ecossistema PAYMENT profissional: segmentos, cobertura país, integração

CREATE TABLE IF NOT EXISTS payment_ecosystem_segment (
    code VARCHAR(40) PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    description TEXT,
    sort_order INTEGER DEFAULT 100 NOT NULL,
    default_protocol VARCHAR(20) DEFAULT 'REST' NOT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS payment_player_country_coverage (
    id VARCHAR(36) PRIMARY KEY,
    player_code VARCHAR(64) NOT NULL,
    country_code VARCHAR(2) NOT NULL,
    coverage_role VARCHAR(40) NOT NULL,
    is_primary_market BOOLEAN DEFAULT false NOT NULL,
    locker_density VARCHAR(20) DEFAULT 'MEDIUM',
    metadata_json JSONB DEFAULT '{}'::jsonb NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    CONSTRAINT uq_ppcc_player_country_role UNIQUE (player_code, country_code, coverage_role)
);
CREATE INDEX IF NOT EXISTS ix_ppcc_country ON payment_player_country_coverage (country_code);
CREATE INDEX IF NOT EXISTS ix_ppcc_player ON payment_player_country_coverage (player_code);

CREATE TABLE IF NOT EXISTS payment_player_integration (
    id VARCHAR(36) PRIMARY KEY,
    player_code VARCHAR(64) NOT NULL UNIQUE,
    integration_protocol VARCHAR(20) DEFAULT 'REST' NOT NULL,
    api_base_url VARCHAR(500),
    webhook_inbound_path VARCHAR(255),
    sandbox_ready BOOLEAN DEFAULT false NOT NULL,
    production_ready BOOLEAN DEFAULT false NOT NULL,
    payment_capture_mode VARCHAR(30) DEFAULT 'CAPTURE_NOW' NOT NULL,
    split_settlement_supported BOOLEAN DEFAULT false NOT NULL,
    cross_border_supported BOOLEAN DEFAULT false NOT NULL,
    readiness_score INTEGER DEFAULT 0 NOT NULL,
    linked_domains_json JSONB DEFAULT '[]'::jsonb NOT NULL,
    integration_notes TEXT,
    metadata_json JSONB DEFAULT '{}'::jsonb NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    CONSTRAINT ck_ppi_readiness CHECK (readiness_score >= 0 AND readiness_score <= 100)
);
CREATE INDEX IF NOT EXISTS ix_ppi_readiness ON payment_player_integration (readiness_score DESC);
