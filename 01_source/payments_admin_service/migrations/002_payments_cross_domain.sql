-- Cross-domain PAYMENT: contexto de pedido, ecossistema mundial, conciliação, holds, vault

CREATE TABLE IF NOT EXISTS payment_ecosystem_player (
    id VARCHAR(36) PRIMARY KEY,
    code VARCHAR(64) NOT NULL UNIQUE,
    name VARCHAR(160) NOT NULL,
    segment VARCHAR(40) NOT NULL,
    countries_json JSONB DEFAULT '[]'::jsonb NOT NULL,
    parent_player_code VARCHAR(64),
    integration_status VARCHAR(20) DEFAULT 'SANDBOX' NOT NULL,
    metadata_json JSONB DEFAULT '{}'::jsonb NOT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_pep_segment ON payment_ecosystem_player (segment);

CREATE TABLE IF NOT EXISTS payment_order_context (
    id VARCHAR(36) PRIMARY KEY,
    order_id VARCHAR(64) NOT NULL UNIQUE,
    tenant_id VARCHAR(36),
    primary_transaction_id VARCHAR(36),
    locker_id VARCHAR(120),
    region_code VARCHAR(20),
    sales_channel VARCHAR(50),
    marketplace_partner_id VARCHAR(36),
    carrier_partner_id VARCHAR(36),
    locker_network_code VARCHAR(64),
    status VARCHAR(30) DEFAULT 'OPEN' NOT NULL,
    total_amount_cents INTEGER DEFAULT 0 NOT NULL,
    currency VARCHAR(8) DEFAULT 'BRL' NOT NULL,
    metadata_json JSONB DEFAULT '{}'::jsonb NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_poc_tenant ON payment_order_context (tenant_id);
CREATE INDEX IF NOT EXISTS ix_poc_locker ON payment_order_context (locker_id);

CREATE TABLE IF NOT EXISTS payment_context_player_link (
    id VARCHAR(36) PRIMARY KEY,
    order_context_id VARCHAR(36) NOT NULL,
    player_code VARCHAR(64) NOT NULL,
    role VARCHAR(40) NOT NULL,
    amount_cents INTEGER,
    share_pct NUMERIC(5, 2),
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_pcpl_context ON payment_context_player_link (order_context_id);

CREATE TABLE IF NOT EXISTS payment_reconciliation_batch (
    id VARCHAR(36) PRIMARY KEY,
    batch_code VARCHAR(64) NOT NULL UNIQUE,
    region_code VARCHAR(20),
    gateway VARCHAR(50),
    period_start DATE,
    period_end DATE,
    status VARCHAR(20) DEFAULT 'OPEN' NOT NULL,
    expected_count INTEGER DEFAULT 0 NOT NULL,
    matched_count INTEGER DEFAULT 0 NOT NULL,
    mismatch_count INTEGER DEFAULT 0 NOT NULL,
    total_amount_cents BIGINT DEFAULT 0 NOT NULL,
    currency VARCHAR(8) DEFAULT 'BRL' NOT NULL,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    closed_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS ix_prb_status ON payment_reconciliation_batch (status);

CREATE TABLE IF NOT EXISTS webhook_deliveries (
    id VARCHAR(36) PRIMARY KEY,
    endpoint_id VARCHAR(36) NOT NULL,
    event_name VARCHAR(100) NOT NULL,
    aggregate_type VARCHAR(50),
    aggregate_id VARCHAR(36),
    payload_json TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'PENDING' NOT NULL,
    attempt_count INTEGER DEFAULT 0 NOT NULL,
    max_attempts INTEGER DEFAULT 5 NOT NULL,
    last_status_code INTEGER,
    last_response_body TEXT,
    last_attempt_at TIMESTAMPTZ,
    next_attempt_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    delivered_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_whd_endpoint ON webhook_deliveries (endpoint_id);
CREATE INDEX IF NOT EXISTS ix_whd_status ON webhook_deliveries (status);

CREATE TABLE IF NOT EXISTS partner_payment_holds (
    id VARCHAR(36) PRIMARY KEY,
    partner_id VARCHAR(36) NOT NULL,
    invoice_id VARCHAR(36) NOT NULL,
    order_id VARCHAR(64),
    hold_amount_cents BIGINT NOT NULL,
    release_schedule VARCHAR(30) DEFAULT 'AFTER_15_DAYS' NOT NULL,
    released_at TIMESTAMPTZ,
    released_amount_cents BIGINT,
    dispute_opened_at TIMESTAMPTZ,
    dispute_resolved_at TIMESTAMPTZ,
    dispute_result VARCHAR(20),
    status VARCHAR(20) DEFAULT 'HELD' NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_pph_partner ON partner_payment_holds (partner_id);

CREATE TABLE IF NOT EXISTS saved_payment_methods (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    method_code VARCHAR(80) NOT NULL,
    gateway_token VARCHAR(255) NOT NULL,
    last4 VARCHAR(4),
    card_brand VARCHAR(50),
    cardholder_name VARCHAR(255),
    expiry_month INTEGER,
    expiry_year INTEGER,
    is_default BOOLEAN DEFAULT false NOT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_spm_user ON saved_payment_methods (user_id);
