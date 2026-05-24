-- Camada Global OPS Fiscal: jurisdições, corredores fiscais, certificações, readiness, SLA, DLQ

CREATE TABLE IF NOT EXISTS fiscal_jurisdictions (
    country VARCHAR(5) PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    currency VARCHAR(8) NOT NULL,
    default_regime VARCHAR(40) NOT NULL,
    vat_label VARCHAR(20) NOT NULL DEFAULT 'VAT',
    authority_name VARCHAR(120),
    active BOOLEAN NOT NULL DEFAULT true,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS fiscal_document_type_catalog (
    id VARCHAR(36) PRIMARY KEY,
    code VARCHAR(40) NOT NULL UNIQUE,
    name VARCHAR(120) NOT NULL,
    country VARCHAR(5) NOT NULL,
    family VARCHAR(30) NOT NULL,
    xml_schema VARCHAR(80),
    requires_a1_cert BOOLEAN NOT NULL DEFAULT false,
    supports_contingency BOOLEAN NOT NULL DEFAULT true,
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    FOREIGN KEY (country) REFERENCES fiscal_jurisdictions(country)
);

CREATE INDEX IF NOT EXISTS ix_fiscal_doc_type_country ON fiscal_document_type_catalog(country, active);

CREATE TABLE IF NOT EXISTS fiscal_tax_corridors (
    id VARCHAR(36) PRIMARY KEY,
    corridor_code VARCHAR(48) NOT NULL UNIQUE,
    name VARCHAR(160) NOT NULL,
    origin_country VARCHAR(5) NOT NULL,
    dest_country VARCHAR(5) NOT NULL,
    primary_issuer_id VARCHAR(36) NOT NULL,
    primary_issuer_code VARCHAR(32) NOT NULL,
    fallback_issuer_id VARCHAR(36),
    fallback_issuer_code VARCHAR(32),
    document_type_code VARCHAR(40) NOT NULL,
    handoff_type VARCHAR(32) NOT NULL DEFAULT 'LOCKER_EMISSION',
    service_level VARCHAR(20) NOT NULL DEFAULT 'STANDARD',
    transit_hours_max INTEGER NOT NULL DEFAULT 72,
    supports_b2b BOOLEAN NOT NULL DEFAULT true,
    supports_b2c BOOLEAN NOT NULL DEFAULT true,
    active BOOLEAN NOT NULL DEFAULT true,
    priority INTEGER NOT NULL DEFAULT 100,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    FOREIGN KEY (origin_country) REFERENCES fiscal_jurisdictions(country),
    FOREIGN KEY (dest_country) REFERENCES fiscal_jurisdictions(country),
    FOREIGN KEY (primary_issuer_id) REFERENCES fiscal_issuer_partners(id),
    FOREIGN KEY (fallback_issuer_id) REFERENCES fiscal_issuer_partners(id)
);

CREATE INDEX IF NOT EXISTS ix_fiscal_corridor_route ON fiscal_tax_corridors(origin_country, dest_country, active);

CREATE TABLE IF NOT EXISTS fiscal_corridor_tax_rules (
    id VARCHAR(36) PRIMARY KEY,
    corridor_id VARCHAR(36) NOT NULL,
    rule_order INTEGER NOT NULL DEFAULT 1,
    tax_code VARCHAR(20) NOT NULL,
    rate_pct NUMERIC(7,4),
    cfop VARCHAR(5),
    ncm_pattern VARCHAR(20),
    notes TEXT,
    FOREIGN KEY (corridor_id) REFERENCES fiscal_tax_corridors(id) ON DELETE CASCADE,
    UNIQUE (corridor_id, rule_order)
);

CREATE TABLE IF NOT EXISTS fiscal_issuer_jurisdiction_grants (
    id VARCHAR(36) PRIMARY KEY,
    issuer_id VARCHAR(36) NOT NULL,
    issuer_code VARCHAR(32) NOT NULL,
    country VARCHAR(5) NOT NULL,
    region_code VARCHAR(20),
    document_type_code VARCHAR(40) NOT NULL,
    grant_status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    valid_from DATE,
    valid_to DATE,
    cert_ref VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    FOREIGN KEY (issuer_id) REFERENCES fiscal_issuer_partners(id) ON DELETE CASCADE,
    FOREIGN KEY (country) REFERENCES fiscal_jurisdictions(country),
    UNIQUE (issuer_id, country, region_code, document_type_code)
);

CREATE TABLE IF NOT EXISTS fiscal_compliance_certifications (
    id VARCHAR(36) PRIMARY KEY,
    issuer_id VARCHAR(36) NOT NULL,
    issuer_code VARCHAR(32) NOT NULL,
    certification_type VARCHAR(40) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'VALID',
    issuer_authority VARCHAR(120),
    issued_at DATE,
    expires_at DATE,
    evidence_url VARCHAR(500),
    scope_notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    FOREIGN KEY (issuer_id) REFERENCES fiscal_issuer_partners(id) ON DELETE CASCADE,
    UNIQUE (issuer_id, certification_type)
);

CREATE TABLE IF NOT EXISTS fiscal_emission_slo_policies (
    id VARCHAR(36) PRIMARY KEY,
    corridor_code VARCHAR(48) NOT NULL,
    metric_name VARCHAR(40) NOT NULL,
    target_p99_ms INTEGER NOT NULL,
    target_success_rate_pct NUMERIC(5,2) NOT NULL DEFAULT 99.50,
    breach_credit_cents INTEGER NOT NULL DEFAULT 0,
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (corridor_code, metric_name)
);

CREATE TABLE IF NOT EXISTS fiscal_integration_readiness (
    issuer_id VARCHAR(36) PRIMARY KEY,
    issuer_code VARCHAR(32) NOT NULL,
    country VARCHAR(5) NOT NULL,
    score_total NUMERIC(5,2) NOT NULL DEFAULT 0,
    score_certificates NUMERIC(5,2) NOT NULL DEFAULT 0,
    score_api NUMERIC(5,2) NOT NULL DEFAULT 0,
    score_contingency NUMERIC(5,2) NOT NULL DEFAULT 0,
    readiness_band CHAR(1) NOT NULL DEFAULT 'D',
    blockers_json TEXT NOT NULL DEFAULT '[]',
    computed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    FOREIGN KEY (issuer_id) REFERENCES fiscal_issuer_partners(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS fiscal_webhook_delivery_log (
    id VARCHAR(36) PRIMARY KEY,
    issuer_id VARCHAR(36) NOT NULL,
    event_type VARCHAR(80) NOT NULL,
    delivery_status VARCHAR(20) NOT NULL,
    http_status INTEGER,
    attempt INTEGER NOT NULL DEFAULT 1,
    payload_hash VARCHAR(64),
    error_message VARCHAR(500),
    next_retry_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    FOREIGN KEY (issuer_id) REFERENCES fiscal_issuer_partners(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_fiscal_webhook_dlq_status ON fiscal_webhook_delivery_log(delivery_status, created_at);

CREATE TABLE IF NOT EXISTS fiscal_auto_classification_rules (
    id VARCHAR(36) PRIMARY KEY,
    sku_pattern VARCHAR(80) NOT NULL,
    category_code VARCHAR(40),
    ncm_code VARCHAR(10) NOT NULL,
    icms_cst VARCHAR(3),
    pis_cst VARCHAR(2),
    cofins_cst VARCHAR(2),
    cfop VARCHAR(5),
    country VARCHAR(5) NOT NULL DEFAULT 'BR',
    priority INTEGER NOT NULL DEFAULT 100,
    source VARCHAR(20) NOT NULL DEFAULT 'MANUAL',
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_fiscal_class_rules_country ON fiscal_auto_classification_rules(country, active, priority);
