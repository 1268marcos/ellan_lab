-- Domínio MONEY & CÂMBIO — nível profissional / cobertura mundial

CREATE TABLE IF NOT EXISTS money_operating_country (
    id BIGSERIAL PRIMARY KEY,
    country_code CHAR(2) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    continent VARCHAR(50),
    default_currency_code CHAR(3) NOT NULL,
    regulatory_zone VARCHAR(20) NOT NULL,
    primary_languages_json JSONB DEFAULT '[]'::jsonb NOT NULL,
    locker_networks_json JSONB DEFAULT '[]'::jsonb NOT NULL,
    metadata_json JSONB DEFAULT '{}'::jsonb NOT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS money_method_country_matrix (
    id BIGSERIAL PRIMARY KEY,
    country_code CHAR(2) NOT NULL,
    payment_method_code VARCHAR(80) NOT NULL,
    min_amount_cents BIGINT DEFAULT 0 NOT NULL,
    max_amount_cents BIGINT,
    is_instant_settlement BOOLEAN DEFAULT false NOT NULL,
    requires_kyc_above_cents BIGINT,
    sort_order INTEGER DEFAULT 100 NOT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    UNIQUE (country_code, payment_method_code)
);

CREATE TABLE IF NOT EXISTS money_wallet_country_matrix (
    id BIGSERIAL PRIMARY KEY,
    country_code CHAR(2) NOT NULL,
    wallet_provider_code VARCHAR(80) NOT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    UNIQUE (country_code, wallet_provider_code)
);

CREATE TABLE IF NOT EXISTS cambio_payment_corridor (
    id VARCHAR(36) PRIMARY KEY,
    corridor_code VARCHAR(48) NOT NULL UNIQUE,
    name VARCHAR(160) NOT NULL,
    origin_country_code CHAR(2) NOT NULL,
    destination_country_code CHAR(2) NOT NULL,
    transaction_currency CHAR(3) NOT NULL,
    settlement_currency CHAR(3) NOT NULL,
    corridor_type VARCHAR(24) DEFAULT 'CROSS_BORDER' NOT NULL,
    default_spread_bps INTEGER DEFAULT 0 NOT NULL,
    fx_partner_code VARCHAR(32),
    notes TEXT,
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS cambio_corridor_markup (
    id VARCHAR(36) PRIMARY KEY,
    corridor_id VARCHAR(36) NOT NULL,
    partner_code VARCHAR(32),
    markup_bps INTEGER DEFAULT 0 NOT NULL,
    valid_from DATE NOT NULL,
    valid_until DATE,
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS money_compliance_limit (
    id VARCHAR(36) PRIMARY KEY,
    country_code CHAR(2) NOT NULL,
    currency_code CHAR(3) NOT NULL,
    limit_type VARCHAR(32) NOT NULL,
    amount_cents BIGINT NOT NULL,
    description VARCHAR(255),
    regulatory_ref VARCHAR(64),
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS cambio_fx_rate_audit (
    id VARCHAR(36) PRIMARY KEY,
    base_currency VARCHAR(8) NOT NULL,
    quote_currency VARCHAR(8) NOT NULL,
    rate_date DATE NOT NULL,
    old_rate NUMERIC(18, 8),
    new_rate NUMERIC(18, 8) NOT NULL,
    source VARCHAR(40) NOT NULL,
    changed_by VARCHAR(80) DEFAULT 'system',
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_mmc_country ON money_method_country_matrix (country_code, is_active);
CREATE INDEX IF NOT EXISTS ix_mwc_country ON money_wallet_country_matrix (country_code, is_active);
CREATE INDEX IF NOT EXISTS ix_cpc_origin_dest ON cambio_payment_corridor (origin_country_code, destination_country_code);
