-- Domínio MONEY & CÂMBIO (alinhado a complete_schema_20260523_d.sql + extensões OPS)

CREATE TABLE IF NOT EXISTS money_currency_catalog (
    id BIGSERIAL PRIMARY KEY,
    code CHAR(3) NOT NULL UNIQUE,
    name VARCHAR(120) NOT NULL,
    symbol VARCHAR(8),
    minor_units INTEGER DEFAULT 2 NOT NULL,
    numeric_code VARCHAR(3),
    region_hint VARCHAR(40),
    metadata_json JSONB DEFAULT '{}'::jsonb NOT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

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

CREATE TABLE IF NOT EXISTS wallet_provider_catalog (
    id BIGSERIAL PRIMARY KEY,
    code VARCHAR(80) NOT NULL UNIQUE,
    name VARCHAR(120) NOT NULL,
    metadata_json JSONB DEFAULT '{}'::jsonb NOT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS cambio_fx_rates (
    id VARCHAR(36) PRIMARY KEY,
    base_currency VARCHAR(8) NOT NULL,
    quote_currency VARCHAR(8) NOT NULL,
    rate_date DATE NOT NULL,
    rate NUMERIC(18, 8) NOT NULL,
    source VARCHAR(40) DEFAULT 'MANUAL' NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    UNIQUE (base_currency, quote_currency, rate_date)
);

CREATE TABLE IF NOT EXISTS money_cambio_integration_partners (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    code VARCHAR(32) NOT NULL UNIQUE,
    partner_type VARCHAR(30) NOT NULL,
    region_code VARCHAR(20),
    api_base_url VARCHAR(500),
    default_currency CHAR(3) DEFAULT 'BRL' NOT NULL,
    country CHAR(2) DEFAULT 'BR' NOT NULL,
    active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS money_cambio_webhook_endpoints (
    id VARCHAR(36) PRIMARY KEY,
    partner_id VARCHAR(36) NOT NULL,
    url VARCHAR(500) NOT NULL,
    secret_hash VARCHAR(128) NOT NULL,
    secret_key VARCHAR(256),
    events_json TEXT DEFAULT '["fx.updated","money.catalog.changed"]' NOT NULL,
    api_version VARCHAR(10) DEFAULT 'v1' NOT NULL,
    active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS money_cambio_api_keys (
    id VARCHAR(36) PRIMARY KEY,
    partner_id VARCHAR(36) NOT NULL,
    key_prefix VARCHAR(16) NOT NULL,
    key_hash VARCHAR(128) NOT NULL,
    label VARCHAR(64),
    scopes_json TEXT DEFAULT '["money:read","cambio:read"]' NOT NULL,
    expires_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_cambio_fx_base_quote ON cambio_fx_rates (base_currency, quote_currency);
