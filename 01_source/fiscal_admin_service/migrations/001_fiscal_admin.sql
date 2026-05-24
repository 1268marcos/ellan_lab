-- DDL alinhado a complete_schema_20260523_d.sql (domínio fiscal + admin emissores)

CREATE TABLE IF NOT EXISTS fiscal_issuer_partners (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    code VARCHAR(32) NOT NULL UNIQUE,
    issuer_type VARCHAR(40) NOT NULL DEFAULT 'SEFAZ',
    country VARCHAR(5) NOT NULL DEFAULT 'BR',
    region_code VARCHAR(20),
    api_base_url VARCHAR(500),
    credentials_secret_ref VARCHAR(255),
    webhook_secret_ref VARCHAR(255),
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS fiscal_issuer_webhook_endpoints (
    id VARCHAR(36) PRIMARY KEY,
    issuer_id VARCHAR(36) NOT NULL,
    url VARCHAR(500) NOT NULL,
    secret_hash VARCHAR(128) NOT NULL,
    secret_key VARCHAR(256),
    events_json TEXT NOT NULL DEFAULT '["fiscal.document.*","fiscal.callback.*"]',
    api_version VARCHAR(10) NOT NULL DEFAULT 'v1',
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_fiscal_issuer_webhook_issuer ON fiscal_issuer_webhook_endpoints (issuer_id);

CREATE TABLE IF NOT EXISTS fiscal_issuer_api_keys (
    id VARCHAR(36) PRIMARY KEY,
    issuer_id VARCHAR(36) NOT NULL,
    key_prefix VARCHAR(16) NOT NULL,
    key_hash VARCHAR(128) NOT NULL,
    label VARCHAR(64),
    scopes_json TEXT NOT NULL DEFAULT '["fiscal:read","fiscal:write"]',
    expires_at TIMESTAMPTZ,
    last_used_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    created_by VARCHAR(36),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_fiscal_issuer_api_keys_issuer ON fiscal_issuer_api_keys (issuer_id);

CREATE TABLE IF NOT EXISTS fiscal_documents (
    id VARCHAR(80) PRIMARY KEY,
    order_id VARCHAR(80) NOT NULL,
    receipt_code VARCHAR(64) NOT NULL,
    document_type VARCHAR(50) NOT NULL,
    channel VARCHAR(20),
    region VARCHAR(10),
    amount_cents INTEGER NOT NULL,
    currency VARCHAR(10) NOT NULL DEFAULT 'BRL',
    delivery_mode VARCHAR(20),
    send_status VARCHAR(50),
    send_target VARCHAR(255),
    print_status VARCHAR(50),
    payload_json TEXT NOT NULL DEFAULT '{}',
    issued_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    tenant_id VARCHAR(64),
    attempt INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS ix_fiscal_documents_order ON fiscal_documents (order_id);

CREATE TABLE IF NOT EXISTS fiscal_reconciliation_gaps (
    id VARCHAR(60) PRIMARY KEY,
    dedupe_key VARCHAR(180) NOT NULL,
    gap_type VARCHAR(80) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL,
    order_id VARCHAR(100),
    invoice_id VARCHAR(50),
    details_json JSONB,
    first_detected_at TIMESTAMPTZ NOT NULL,
    last_detected_at TIMESTAMPTZ NOT NULL,
    resolved_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS fiscal_provider_health_status (
    country VARCHAR(5) PRIMARY KEY,
    provider_name VARCHAR(80) NOT NULL,
    mode VARCHAR(20) NOT NULL,
    enabled BOOLEAN NOT NULL,
    base_url VARCHAR(300),
    last_status VARCHAR(20) NOT NULL,
    last_http_status INTEGER,
    last_latency_ms INTEGER,
    last_error VARCHAR(1000),
    checked_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS fiscal_accounting_approvals (
    id VARCHAR(80) PRIMARY KEY,
    owner VARCHAR(160) NOT NULL,
    eta TIMESTAMPTZ,
    status VARCHAR(80) NOT NULL,
    payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS fiscal_authority_callbacks (
    id VARCHAR(60) PRIMARY KEY,
    invoice_id VARCHAR(50) NOT NULL,
    authority VARCHAR(30) NOT NULL,
    event_type VARCHAR(80),
    status VARCHAR(40),
    protocol_number VARCHAR(120),
    raw_payload JSONB,
    received_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS product_fiscal_config (
    sku_id VARCHAR(255) PRIMARY KEY,
    ncm_code VARCHAR(10),
    cest VARCHAR(9),
    icms_cst VARCHAR(3),
    pis_cst VARCHAR(2),
    cofins_cst VARCHAR(2),
    iva_category VARCHAR(20),
    is_active BOOLEAN NOT NULL DEFAULT true,
    cfop VARCHAR(5),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS tenant_fiscal_config (
    tenant_id VARCHAR(100) PRIMARY KEY,
    cnpj VARCHAR(18) NOT NULL,
    razao_social VARCHAR(140) NOT NULL,
    ie VARCHAR(20),
    regime VARCHAR(20) NOT NULL,
    crt CHAR(1) NOT NULL,
    cert_a1_ref VARCHAR(255),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    brand_config JSONB DEFAULT '{}'::jsonb
);
