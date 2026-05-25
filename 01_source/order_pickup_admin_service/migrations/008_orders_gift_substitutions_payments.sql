-- Substituições, gift pickup e espelho de payment_transactions (gateway)

CREATE TABLE IF NOT EXISTS order_item_substitutions (
    id VARCHAR(36) PRIMARY KEY,
    order_id VARCHAR(64) NOT NULL,
    order_item_id VARCHAR(36),
    original_sku_id VARCHAR(255) NOT NULL,
    substitute_sku_id VARCHAR(255) NOT NULL,
    reason_code VARCHAR(40) NOT NULL,
    status VARCHAR(20) DEFAULT 'REQUESTED' NOT NULL,
    quantity INTEGER DEFAULT 1 NOT NULL,
    approved_by VARCHAR(64),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_opa_subst_order ON order_item_substitutions (order_id);

CREATE TABLE IF NOT EXISTS order_gift_pickup (
    id VARCHAR(36) PRIMARY KEY,
    order_id VARCHAR(64) NOT NULL UNIQUE,
    is_gift BOOLEAN DEFAULT true NOT NULL,
    purchaser_name VARCHAR(200),
    recipient_name VARCHAR(200) NOT NULL,
    recipient_phone_masked VARCHAR(32),
    recipient_document_masked VARCHAR(32),
    pickup_authorization_code VARCHAR(32),
    id_verification_required BOOLEAN DEFAULT true NOT NULL,
    status VARCHAR(30) DEFAULT 'PENDING_VERIFICATION' NOT NULL,
    verified_at TIMESTAMPTZ,
    picked_up_at TIMESTAMPTZ,
    message TEXT,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS payment_transactions (
    id VARCHAR(36) PRIMARY KEY,
    order_id VARCHAR(64) NOT NULL,
    gateway VARCHAR(50) NOT NULL,
    gateway_transaction_id VARCHAR(128),
    amount_cents INTEGER NOT NULL,
    currency VARCHAR(8) DEFAULT 'BRL' NOT NULL,
    payment_method VARCHAR(30) NOT NULL,
    status VARCHAR(20) DEFAULT 'INITIATED' NOT NULL,
    gateway_fee_cents INTEGER DEFAULT 0 NOT NULL,
    net_amount_cents INTEGER,
    reconciliation_status VARCHAR(20) DEFAULT 'PENDING',
    approved_at TIMESTAMPTZ,
    synced_at TIMESTAMPTZ,
    source VARCHAR(20) DEFAULT 'LOCAL' NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_opa_paytx_order ON payment_transactions (order_id);
CREATE INDEX IF NOT EXISTS idx_opa_paytx_status ON payment_transactions (status);
