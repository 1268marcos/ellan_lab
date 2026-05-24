-- DDL alinhado a complete_schema_20260524_a.sql (domínio PAYMENT transacional)

CREATE TABLE IF NOT EXISTS payment_transactions (
    id VARCHAR(36) PRIMARY KEY,
    order_id VARCHAR(36) NOT NULL,
    gateway VARCHAR(50) NOT NULL,
    gateway_transaction_id VARCHAR(128),
    gateway_idempotency_key VARCHAR(128),
    amount_cents INTEGER NOT NULL,
    currency VARCHAR(8) DEFAULT 'BRL' NOT NULL,
    payment_method VARCHAR(30) NOT NULL,
    card_brand VARCHAR(20),
    card_last4 VARCHAR(4),
    card_type VARCHAR(10),
    installments INTEGER DEFAULT 1 NOT NULL,
    status VARCHAR(20) DEFAULT 'INITIATED' NOT NULL,
    error_code VARCHAR(100),
    error_message TEXT,
    reconciliation_status VARCHAR(20) DEFAULT 'PENDING' NOT NULL,
    reconciliation_batch_id VARCHAR(100),
    gateway_fee_cents INTEGER DEFAULT 0,
    net_amount_cents INTEGER,
    initiated_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_pay_tx_order ON payment_transactions (order_id);
CREATE INDEX IF NOT EXISTS ix_pay_tx_status ON payment_transactions (status);

CREATE TABLE IF NOT EXISTS payment_instructions (
    id VARCHAR(36) PRIMARY KEY,
    order_id VARCHAR(36) NOT NULL,
    instruction_type VARCHAR(50) NOT NULL,
    amount_cents INTEGER NOT NULL,
    currency VARCHAR(8) DEFAULT 'BRL' NOT NULL,
    status VARCHAR(30) DEFAULT 'PENDING' NOT NULL,
    expires_at TIMESTAMPTZ,
    qr_code_text TEXT,
    provider_payment_id TEXT,
    provider_name TEXT,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_pay_inst_order ON payment_instructions (order_id);

CREATE TABLE IF NOT EXISTS payment_splits (
    id VARCHAR(36) PRIMARY KEY,
    order_id VARCHAR(36) NOT NULL,
    recipient_type VARCHAR(30) NOT NULL,
    recipient_id VARCHAR(36) NOT NULL,
    amount_cents INTEGER NOT NULL,
    percentage NUMERIC(5, 2),
    status VARCHAR(20) DEFAULT 'PENDING' NOT NULL,
    settled_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_pay_split_order ON payment_splits (order_id);

CREATE TABLE IF NOT EXISTS payments (
    id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    provider_payment_id TEXT,
    method TEXT NOT NULL,
    status TEXT NOT NULL,
    amount_cents INTEGER NOT NULL,
    currency TEXT DEFAULT 'EUR' NOT NULL,
    created_at BIGINT NOT NULL,
    confirmed_at BIGINT,
    idempotency_key TEXT,
    raw_json JSONB DEFAULT '{}'::jsonb NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_payments_order ON payments (order_id);

CREATE TABLE IF NOT EXISTS webhook_endpoints (
    id VARCHAR(36) PRIMARY KEY,
    partner_type VARCHAR(20) NOT NULL,
    partner_id VARCHAR(36) NOT NULL,
    url VARCHAR(500) NOT NULL,
    events TEXT NOT NULL,
    secret_ref VARCHAR(255),
    signing_algo VARCHAR(20) DEFAULT 'HMAC_SHA256' NOT NULL,
    active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_webhook_partner ON webhook_endpoints (partner_type, partner_id);

CREATE TABLE IF NOT EXISTS gateway_events (
    id TEXT PRIMARY KEY,
    gateway_id TEXT NOT NULL,
    region TEXT NOT NULL,
    locker_id TEXT NOT NULL,
    porta INTEGER,
    event_type TEXT NOT NULL,
    created_at BIGINT NOT NULL,
    request_id TEXT,
    order_id TEXT,
    payload_json JSONB DEFAULT '{}'::jsonb NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_gw_ev_order ON gateway_events (order_id);
