CREATE TABLE IF NOT EXISTS order_ops_timeline (
    id VARCHAR(36) PRIMARY KEY,
    order_id VARCHAR(64) NOT NULL,
    event_source VARCHAR(40) NOT NULL,
    event_type VARCHAR(80) NOT NULL,
    severity VARCHAR(20) DEFAULT 'INFO' NOT NULL,
    title VARCHAR(200) NOT NULL,
    detail_json TEXT DEFAULT '{}' NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_opa_timeline_order ON order_ops_timeline (order_id, occurred_at DESC);

CREATE TABLE IF NOT EXISTS order_sla_watches (
    id VARCHAR(36) PRIMARY KEY,
    order_id VARCHAR(64) NOT NULL,
    watch_type VARCHAR(40) NOT NULL,
    due_at TIMESTAMPTZ NOT NULL,
    status VARCHAR(20) DEFAULT 'ACTIVE' NOT NULL,
    breached_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,
    breach_reason VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_opa_sla_order ON order_sla_watches (order_id);
CREATE INDEX IF NOT EXISTS idx_opa_sla_due ON order_sla_watches (due_at, status);

CREATE TABLE IF NOT EXISTS order_disputes (
    id VARCHAR(36) PRIMARY KEY,
    order_id VARCHAR(64) NOT NULL,
    dispute_type VARCHAR(30) NOT NULL,
    status VARCHAR(20) DEFAULT 'OPEN' NOT NULL,
    amount_cents INTEGER,
    currency VARCHAR(8) DEFAULT 'BRL',
    reason_code VARCHAR(64),
    notes TEXT,
    opened_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_opa_disputes_order ON order_disputes (order_id);

CREATE TABLE IF NOT EXISTS order_integration_health (
    id VARCHAR(36) PRIMARY KEY,
    channel_code VARCHAR(32) NOT NULL,
    check_type VARCHAR(40) DEFAULT 'WEBHOOK_DELIVERY' NOT NULL,
    status VARCHAR(20) NOT NULL,
    latency_ms INTEGER,
    last_error TEXT,
    checked_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_opa_health_channel ON order_integration_health (channel_code, checked_at DESC);
