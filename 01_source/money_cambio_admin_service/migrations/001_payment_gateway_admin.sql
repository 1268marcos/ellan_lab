-- DDL alinhado a complete_schema_20260521_c.sql + tabelas admin PSP

CREATE TABLE IF NOT EXISTS payment_method_catalog (
    id BIGSERIAL PRIMARY KEY,
    code VARCHAR(80) NOT NULL UNIQUE,
    name VARCHAR(120) NOT NULL,
    family VARCHAR(80),
    is_wallet BOOLEAN DEFAULT false NOT NULL,
    is_card BOOLEAN DEFAULT false NOT NULL,
    is_bnpl BOOLEAN DEFAULT false NOT NULL,
    is_cash_like BOOLEAN DEFAULT false NOT NULL,
    is_bank_transfer BOOLEAN DEFAULT false NOT NULL,
    is_instant BOOLEAN DEFAULT false NOT NULL,
    metadata_json JSONB DEFAULT '{}'::jsonb NOT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS payment_interface_catalog (
    id BIGSERIAL PRIMARY KEY,
    code VARCHAR(80) NOT NULL UNIQUE,
    name VARCHAR(120) NOT NULL,
    interface_type VARCHAR(60),
    requires_hw BOOLEAN DEFAULT false NOT NULL,
    metadata_json JSONB DEFAULT '{}'::jsonb NOT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS payment_method_ui_alias (
    id TEXT PRIMARY KEY,
    ui_code TEXT NOT NULL,
    canonical_method_code TEXT NOT NULL,
    default_payment_interface_code TEXT,
    default_wallet_provider_code TEXT,
    requires_customer_phone BOOLEAN DEFAULT false NOT NULL,
    requires_wallet_provider BOOLEAN DEFAULT false NOT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS locker_payment_methods (
    locker_id VARCHAR(120) NOT NULL,
    method VARCHAR(64) NOT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMP DEFAULT now() NOT NULL,
    updated_at TIMESTAMP DEFAULT now() NOT NULL,
    PRIMARY KEY (locker_id, method)
);

CREATE TABLE IF NOT EXISTS payment_gateway_device_registry (
    device_hash TEXT PRIMARY KEY,
    version TEXT NOT NULL,
    first_seen_at_epoch BIGINT NOT NULL,
    last_seen_at_epoch BIGINT NOT NULL,
    seen_count INTEGER DEFAULT 1 NOT NULL,
    region_code VARCHAR(20),
    locker_id VARCHAR(120),
    flags_json JSONB DEFAULT '{}'::jsonb NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS payment_gateway_idempotency_keys (
    id TEXT PRIMARY KEY,
    endpoint TEXT NOT NULL,
    idem_key TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    response_blob JSONB DEFAULT '{}'::jsonb NOT NULL,
    status TEXT NOT NULL,
    region_code VARCHAR(20),
    sales_channel VARCHAR(50),
    request_fingerprint TEXT,
    created_at_epoch BIGINT NOT NULL,
    expires_at_epoch BIGINT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_pg_gateway_idem_endpoint_key
    ON payment_gateway_idempotency_keys (endpoint, idem_key);

CREATE TABLE IF NOT EXISTS payment_gateway_risk_events (
    id TEXT PRIMARY KEY,
    request_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    decision TEXT NOT NULL,
    score INTEGER NOT NULL,
    policy_id TEXT NOT NULL,
    region_code VARCHAR(20) NOT NULL,
    locker_id VARCHAR(120) NOT NULL,
    slot INTEGER NOT NULL,
    audit_event_id TEXT NOT NULL,
    reasons_json JSONB DEFAULT '[]'::jsonb NOT NULL,
    signals_json JSONB DEFAULT '{}'::jsonb NOT NULL,
    metadata_json JSONB DEFAULT '{}'::jsonb NOT NULL,
    created_at_epoch BIGINT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS payment_provider_partners (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    code VARCHAR(32) NOT NULL UNIQUE,
    provider_type VARCHAR(30) NOT NULL,
    region_code VARCHAR(20),
    api_base_url VARCHAR(500),
    credentials_secret_ref VARCHAR(255),
    webhook_secret_ref VARCHAR(255),
    currency VARCHAR(8) DEFAULT 'BRL' NOT NULL,
    country VARCHAR(2) DEFAULT 'BR' NOT NULL,
    active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS payment_provider_webhook_endpoints (
    id VARCHAR(36) PRIMARY KEY,
    provider_id VARCHAR(36) NOT NULL,
    url VARCHAR(500) NOT NULL,
    secret_hash VARCHAR(128) NOT NULL,
    secret_key VARCHAR(256),
    events_json TEXT DEFAULT '["payment.*"]' NOT NULL,
    api_version VARCHAR(10) DEFAULT 'v1' NOT NULL,
    retry_policy TEXT DEFAULT '{}' NOT NULL,
    active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS payment_provider_api_keys (
    id VARCHAR(36) PRIMARY KEY,
    provider_id VARCHAR(36) NOT NULL,
    key_prefix VARCHAR(16) NOT NULL,
    key_hash VARCHAR(128) NOT NULL,
    label VARCHAR(64),
    scopes_json TEXT DEFAULT '["payments:write"]' NOT NULL,
    expires_at TIMESTAMPTZ,
    last_used_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    created_by VARCHAR(36),
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_ppgak_provider ON payment_provider_api_keys (provider_id);
