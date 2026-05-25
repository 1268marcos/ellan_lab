-- Prompt 7: capacidades OPS não cobertas (devolução, notificações, pagamento, holds)

CREATE TABLE IF NOT EXISTS order_returns (
    id VARCHAR(36) PRIMARY KEY,
    order_id VARCHAR(64) NOT NULL,
    return_type VARCHAR(30) DEFAULT 'LOCKER_DROP_OFF' NOT NULL,
    status VARCHAR(20) DEFAULT 'REQUESTED' NOT NULL,
    reason_code VARCHAR(64),
    refund_amount_cents INTEGER,
    currency VARCHAR(8) DEFAULT 'BRL' NOT NULL,
    locker_id VARCHAR(120),
    tracking_code VARCHAR(128),
    requested_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    received_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_opa_returns_order ON order_returns (order_id);
CREATE INDEX IF NOT EXISTS idx_opa_returns_status ON order_returns (status);

CREATE TABLE IF NOT EXISTS order_notification_logs (
    id VARCHAR(36) PRIMARY KEY,
    order_id VARCHAR(64) NOT NULL,
    channel VARCHAR(20) NOT NULL,
    template_code VARCHAR(64) NOT NULL,
    recipient_masked VARCHAR(120),
    status VARCHAR(20) DEFAULT 'SENT' NOT NULL,
    provider_ref VARCHAR(128),
    payload_json TEXT DEFAULT '{}' NOT NULL,
    sent_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_opa_notif_order ON order_notification_logs (order_id, sent_at DESC);

CREATE TABLE IF NOT EXISTS order_payment_reconciliation (
    id VARCHAR(36) PRIMARY KEY,
    order_id VARCHAR(64) NOT NULL,
    payment_ref VARCHAR(128),
    expected_cents INTEGER NOT NULL,
    captured_cents INTEGER NOT NULL,
    fee_cents INTEGER DEFAULT 0 NOT NULL,
    currency VARCHAR(8) DEFAULT 'BRL' NOT NULL,
    status VARCHAR(20) DEFAULT 'PENDING' NOT NULL,
    mismatch_reason VARCHAR(255),
    reconciled_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_opa_recon_order ON order_payment_reconciliation (order_id);
CREATE INDEX IF NOT EXISTS idx_opa_recon_status ON order_payment_reconciliation (status);

CREATE TABLE IF NOT EXISTS order_ops_holds (
    id VARCHAR(36) PRIMARY KEY,
    order_id VARCHAR(64) NOT NULL,
    hold_type VARCHAR(40) NOT NULL,
    status VARCHAR(20) DEFAULT 'ACTIVE' NOT NULL,
    reason TEXT,
    placed_by VARCHAR(64) DEFAULT 'ops' NOT NULL,
    released_by VARCHAR(64),
    placed_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    released_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_opa_holds_order ON order_ops_holds (order_id);
CREATE INDEX IF NOT EXISTS idx_opa_holds_active ON order_ops_holds (status) WHERE status = 'ACTIVE';
