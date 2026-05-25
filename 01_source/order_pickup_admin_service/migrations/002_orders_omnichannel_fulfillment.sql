CREATE TABLE IF NOT EXISTS omnichannel_orders (
    id VARCHAR(36) PRIMARY KEY,
    order_id VARCHAR(64) NOT NULL,
    store_id VARCHAR(36) NOT NULL,
    pickup_type VARCHAR(20) DEFAULT 'LOCKER_DELIVERY' NOT NULL,
    status VARCHAR(20) DEFAULT 'PENDING' NOT NULL,
    ready_at TIMESTAMPTZ,
    picked_up_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_opa_omni_order ON omnichannel_orders (order_id);

CREATE TABLE IF NOT EXISTS fulfillment_orders (
    id VARCHAR(36) PRIMARY KEY,
    order_id VARCHAR(64) NOT NULL,
    fulfillment_center_id VARCHAR(36) NOT NULL,
    status VARCHAR(30) DEFAULT 'PENDING' NOT NULL,
    priority INTEGER DEFAULT 100 NOT NULL,
    picked_at TIMESTAMPTZ,
    packed_at TIMESTAMPTZ,
    shipped_at TIMESTAMPTZ,
    delivered_to_locker_at TIMESTAMPTZ,
    tracking_code VARCHAR(128),
    carrier VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_opa_fulfillment_order ON fulfillment_orders (order_id);
