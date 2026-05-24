-- Funcionalidades de valor PAYMENT (roadmap, settlement, compliance, routing, incidentes)

CREATE TABLE IF NOT EXISTS payment_integration_milestone (
    id VARCHAR(36) PRIMARY KEY,
    player_code VARCHAR(64) NOT NULL,
    phase VARCHAR(30) NOT NULL,
    title VARCHAR(200) NOT NULL,
    status VARCHAR(20) DEFAULT 'PLANNED' NOT NULL,
    target_date DATE,
    completed_at TIMESTAMPTZ,
    owner_team VARCHAR(80),
    blockers_json JSONB DEFAULT '[]'::jsonb NOT NULL,
    metadata_json JSONB DEFAULT '{}'::jsonb NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    CONSTRAINT ck_pim_phase CHECK (
        phase IN ('DISCOVERY', 'SANDBOX', 'CERTIFICATION', 'PILOT', 'PRODUCTION', 'OPTIMIZATION')
    ),
    CONSTRAINT ck_pim_status CHECK (status IN ('PLANNED', 'IN_PROGRESS', 'DONE', 'BLOCKED', 'CANCELLED'))
);
CREATE INDEX IF NOT EXISTS ix_pim_player ON payment_integration_milestone (player_code);
CREATE INDEX IF NOT EXISTS ix_pim_status ON payment_integration_milestone (status);

CREATE TABLE IF NOT EXISTS payment_settlement_corridor (
    id VARCHAR(36) PRIMARY KEY,
    corridor_code VARCHAR(64) NOT NULL UNIQUE,
    origin_country VARCHAR(2) NOT NULL,
    destination_country VARCHAR(2) NOT NULL,
    source_player_code VARCHAR(64) NOT NULL,
    settlement_player_code VARCHAR(64) NOT NULL,
    source_currency VARCHAR(8) NOT NULL,
    settlement_currency VARCHAR(8) NOT NULL,
    fx_provider_code VARCHAR(64),
    fee_basis_points INTEGER DEFAULT 0 NOT NULL,
    settlement_delay_days INTEGER DEFAULT 2 NOT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL,
    metadata_json JSONB DEFAULT '{}'::jsonb NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_psc_origin_dest ON payment_settlement_corridor (origin_country, destination_country);

CREATE TABLE IF NOT EXISTS payment_player_compliance (
    id VARCHAR(36) PRIMARY KEY,
    player_code VARCHAR(64) NOT NULL,
    country_code VARCHAR(2) NOT NULL,
    regulatory_framework VARCHAR(40) NOT NULL,
    kyc_level VARCHAR(20) DEFAULT 'STANDARD' NOT NULL,
    pci_scope VARCHAR(20) DEFAULT 'SAQ_A' NOT NULL,
    gdpr_ready BOOLEAN DEFAULT false NOT NULL,
    local_license_ref VARCHAR(120),
    audit_status VARCHAR(20) DEFAULT 'PENDING' NOT NULL,
    last_audit_at DATE,
    risk_tier VARCHAR(10) DEFAULT 'MEDIUM' NOT NULL,
    notes TEXT,
    metadata_json JSONB DEFAULT '{}'::jsonb NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    CONSTRAINT uq_ppc_player_country_framework UNIQUE (player_code, country_code, regulatory_framework)
);
CREATE INDEX IF NOT EXISTS ix_ppc_country ON payment_player_compliance (country_code);

CREATE TABLE IF NOT EXISTS payment_routing_rule (
    id VARCHAR(36) PRIMARY KEY,
    rule_code VARCHAR(64) NOT NULL UNIQUE,
    tenant_id VARCHAR(36),
    country_code VARCHAR(2) NOT NULL,
    payment_method VARCHAR(40) NOT NULL,
    sales_channel VARCHAR(50),
    primary_player_code VARCHAR(64) NOT NULL,
    fallback_player_code VARCHAR(64),
    priority INTEGER DEFAULT 100 NOT NULL,
    min_amount_cents INTEGER,
    max_amount_cents INTEGER,
    is_active BOOLEAN DEFAULT true NOT NULL,
    rationale TEXT,
    metadata_json JSONB DEFAULT '{}'::jsonb NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_prr_country_method ON payment_routing_rule (country_code, payment_method);

CREATE TABLE IF NOT EXISTS payment_integration_incident (
    id VARCHAR(36) PRIMARY KEY,
    player_code VARCHAR(64) NOT NULL,
    severity VARCHAR(10) NOT NULL,
    incident_type VARCHAR(40) NOT NULL,
    title VARCHAR(200) NOT NULL,
    status VARCHAR(20) DEFAULT 'OPEN' NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    resolved_at TIMESTAMPTZ,
    impact_pct NUMERIC(5, 2),
    affected_orders_estimate INTEGER,
    root_cause TEXT,
    metadata_json JSONB DEFAULT '{}'::jsonb NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    CONSTRAINT ck_pii_severity CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL'))
);
CREATE INDEX IF NOT EXISTS ix_pii_player_status ON payment_integration_incident (player_code, status);
