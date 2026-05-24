-- Money & Câmbio — operações avançadas: rails, trava FX, log de cotações

CREATE TABLE IF NOT EXISTS money_player_payment_rail (
    id VARCHAR(36) PRIMARY KEY,
    player_code VARCHAR(48) NOT NULL,
    country_code CHAR(2) NOT NULL,
    payment_method_code VARCHAR(80),
    wallet_provider_code VARCHAR(80),
    channel VARCHAR(16) DEFAULT 'LOCKER' NOT NULL,
    is_enabled BOOLEAN DEFAULT true NOT NULL,
    max_amount_cents BIGINT,
    notes TEXT,
    metadata_json JSONB DEFAULT '{}'::jsonb NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    UNIQUE (player_code, country_code, payment_method_code, wallet_provider_code, channel)
);

CREATE INDEX IF NOT EXISTS ix_mppr_player ON money_player_payment_rail (player_code, country_code);

CREATE TABLE IF NOT EXISTS money_fx_lock (
    id VARCHAR(36) PRIMARY KEY,
    lock_reference VARCHAR(48) NOT NULL UNIQUE,
    player_code VARCHAR(48),
    corridor_code VARCHAR(48) NOT NULL,
    base_currency CHAR(8) NOT NULL,
    quote_currency CHAR(8) NOT NULL,
    locked_rate NUMERIC(18, 8) NOT NULL,
    spread_bps INTEGER DEFAULT 0 NOT NULL,
    amount_cents_ref BIGINT,
    status VARCHAR(16) DEFAULT 'ACTIVE' NOT NULL,
    locked_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_mfl_status ON money_fx_lock (status, expires_at);

CREATE TABLE IF NOT EXISTS money_ops_quote_log (
    id VARCHAR(36) PRIMARY KEY,
    quote_type VARCHAR(32) NOT NULL,
    player_code VARCHAR(48),
    corridor_code VARCHAR(48),
    request_json JSONB DEFAULT '{}'::jsonb NOT NULL,
    result_json JSONB DEFAULT '{}'::jsonb NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_moql_type_created ON money_ops_quote_log (quote_type, created_at DESC);
