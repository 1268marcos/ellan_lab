-- DDL alinhado a complete_schema_20260521_c.sql (order_pickup_service)

CREATE TABLE IF NOT EXISTS ecommerce_partners (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    code VARCHAR(32) NOT NULL UNIQUE,
    integration_type VARCHAR(30) NOT NULL,
    api_base_url VARCHAR(500),
    credentials_secret_ref VARCHAR(255),
    webhook_secret_ref VARCHAR(255),
    revenue_share_pct NUMERIC(6,4),
    currency VARCHAR(8) DEFAULT 'BRL' NOT NULL,
    sla_pickup_hours INTEGER DEFAULT 72 NOT NULL,
    active BOOLEAN DEFAULT true NOT NULL,
    country VARCHAR(2) DEFAULT 'BR' NOT NULL,
    status VARCHAR(30) DEFAULT 'DRAFT' NOT NULL,
    legal_name VARCHAR(140),
    tax_id VARCHAR(32),
    tier VARCHAR(20) DEFAULT 'STANDARD',
    support_email VARCHAR(128),
    support_phone VARCHAR(32),
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS logistics_partners (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    code VARCHAR(32) NOT NULL UNIQUE,
    integration_type VARCHAR(30) NOT NULL,
    api_base_url VARCHAR(500),
    tracking_url_template VARCHAR(500),
    auth_type VARCHAR(20),
    credentials_secret_ref VARCHAR(255),
    default_sla_hours INTEGER DEFAULT 72 NOT NULL,
    reminder_hours_before INTEGER DEFAULT 24 NOT NULL,
    active BOOLEAN DEFAULT true NOT NULL,
    country VARCHAR(2) DEFAULT 'BR' NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS partner_webhook_endpoints (
    id VARCHAR(36) PRIMARY KEY,
    partner_id VARCHAR(36) NOT NULL,
    partner_type VARCHAR(20) NOT NULL,
    url VARCHAR(500) NOT NULL,
    secret_hash VARCHAR(128) NOT NULL,
    secret_key VARCHAR(256),
    events_json TEXT DEFAULT '["*"]' NOT NULL,
    api_version VARCHAR(10) DEFAULT 'v1' NOT NULL,
    retry_policy TEXT DEFAULT '{}' NOT NULL,
    active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS partner_api_keys (
    id VARCHAR(36) PRIMARY KEY,
    partner_id VARCHAR(36) NOT NULL,
    partner_type VARCHAR(20) NOT NULL,
    key_prefix VARCHAR(16) NOT NULL,
    key_hash VARCHAR(128) NOT NULL,
    label VARCHAR(64),
    scopes_json TEXT DEFAULT '[]' NOT NULL,
    expires_at TIMESTAMPTZ,
    last_used_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    created_by VARCHAR(36),
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    id VARCHAR(64) PRIMARY KEY,
    channel VARCHAR(32) NOT NULL,
    region VARCHAR(32) NOT NULL,
    totem_id VARCHAR(100) NOT NULL,
    amount_cents INTEGER NOT NULL,
    currency VARCHAR(8) DEFAULT 'BRL' NOT NULL,
    status VARCHAR(32) NOT NULL,
    payment_status VARCHAR(32) NOT NULL,
    ecommerce_partner_id VARCHAR(100),
    tenant_id VARCHAR(100),
    partner_order_ref VARCHAR(255),
    sku_id VARCHAR(255),
    locker_id VARCHAR(120),
    pickup_deadline_at TIMESTAMPTZ,
    paid_at TIMESTAMPTZ,
    picked_up_at TIMESTAMPTZ,
    order_metadata TEXT DEFAULT '{}' NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS pickups (
    id VARCHAR(64) PRIMARY KEY,
    order_id VARCHAR(64) NOT NULL,
    channel VARCHAR(32) NOT NULL,
    region VARCHAR(32) NOT NULL,
    locker_id VARCHAR(120),
    slot VARCHAR(32),
    status VARCHAR(32) NOT NULL,
    lifecycle_stage VARCHAR(40) NOT NULL,
    expires_at TIMESTAMPTZ,
    ready_at TIMESTAMPTZ,
    redeemed_at TIMESTAMPTZ,
    fraud_flag BOOLEAN DEFAULT false NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS credits (
    id VARCHAR(64) PRIMARY KEY,
    order_id VARCHAR(64) NOT NULL,
    user_id VARCHAR(64) NOT NULL,
    type VARCHAR(32) NOT NULL,
    amount_cents INTEGER NOT NULL,
    currency VARCHAR(8) DEFAULT 'BRL' NOT NULL,
    status VARCHAR(32) DEFAULT 'AVAILABLE' NOT NULL,
    created_at_epoch BIGINT NOT NULL,
    expires_at TIMESTAMPTZ,
    meta_json TEXT DEFAULT '{}' NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS partner_order_events_outbox (
    id VARCHAR(36) PRIMARY KEY,
    partner_id VARCHAR(36) NOT NULL,
    order_id VARCHAR(64) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    payload_json TEXT DEFAULT '{}' NOT NULL,
    status VARCHAR(20) DEFAULT 'PENDING' NOT NULL,
    attempt_count INTEGER DEFAULT 0 NOT NULL,
    max_attempts INTEGER DEFAULT 5 NOT NULL,
    next_retry_at TIMESTAMPTZ,
    last_error TEXT,
    delivered_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS order_fulfillment_tracking (
    id VARCHAR(36) PRIMARY KEY,
    order_id VARCHAR(64) NOT NULL,
    fulfillment_type VARCHAR(30) DEFAULT 'ECOMMERCE_PARTNER' NOT NULL,
    partner_id VARCHAR(36),
    status VARCHAR(30) DEFAULT 'PENDING' NOT NULL,
    last_event_type VARCHAR(50),
    last_outbox_status VARCHAR(20),
    allocated_at TIMESTAMPTZ,
    dispensed_at TIMESTAMPTZ,
    picked_up_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_opa_orders_partner ON orders (ecommerce_partner_id);
CREATE INDEX IF NOT EXISTS idx_opa_pickups_order ON pickups (order_id);
CREATE INDEX IF NOT EXISTS idx_opa_outbox_status ON partner_order_events_outbox (status);

CREATE TABLE IF NOT EXISTS order_items (
    id VARCHAR(36) PRIMARY KEY,
    order_id VARCHAR(64) NOT NULL,
    sku_id VARCHAR(255) NOT NULL,
    sku_description VARCHAR(500),
    quantity INTEGER DEFAULT 1 NOT NULL,
    unit_amount_cents INTEGER NOT NULL,
    total_amount_cents INTEGER NOT NULL,
    item_status VARCHAR(32) DEFAULT 'PENDING' NOT NULL,
    metadata_json TEXT DEFAULT '{}' NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS pickup_events (
    id VARCHAR(36) PRIMARY KEY,
    pickup_id VARCHAR(64) NOT NULL,
    version BIGINT DEFAULT 1 NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    payload_json TEXT DEFAULT '{}' NOT NULL,
    source VARCHAR(100) DEFAULT 'admin' NOT NULL,
    occurred_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS pickup_tokens (
    id VARCHAR(36) PRIMARY KEY,
    order_id VARCHAR(64) NOT NULL,
    pickup_id VARCHAR(64),
    token_hash VARCHAR(128),
    expires_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT true NOT NULL,
    manual_code VARCHAR(32),
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS pickup_attempts (
    id VARCHAR(64) PRIMARY KEY,
    order_id VARCHAR(64) NOT NULL,
    gateway_id VARCHAR(64) DEFAULT '' NOT NULL,
    created_at_epoch BIGINT NOT NULL,
    ok BOOLEAN DEFAULT false NOT NULL,
    reason VARCHAR(255),
    payload_json TEXT DEFAULT '{}' NOT NULL
);

CREATE TABLE IF NOT EXISTS domain_event_outbox (
    id VARCHAR(36) PRIMARY KEY,
    event_key VARCHAR(255) NOT NULL,
    aggregate_type VARCHAR(100),
    aggregate_id VARCHAR(100),
    event_name VARCHAR(100),
    event_version INTEGER DEFAULT 1,
    status VARCHAR(50) DEFAULT 'PENDING' NOT NULL,
    payload_json TEXT DEFAULT '{}' NOT NULL,
    occurred_at TIMESTAMPTZ,
    published_at TIMESTAMPTZ,
    last_error TEXT,
    retry_count INTEGER DEFAULT 0 NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);
