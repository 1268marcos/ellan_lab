CREATE TABLE IF NOT EXISTS food_delivery_orders (
    id VARCHAR(36) PRIMARY KEY,
    order_id VARCHAR(64) NOT NULL,
    platform_code VARCHAR(32) NOT NULL,
    external_order_ref VARCHAR(255),
    restaurant_id VARCHAR(36),
    status VARCHAR(30) DEFAULT 'PLACED' NOT NULL,
    temperature_zone VARCHAR(20) DEFAULT 'HOT' NOT NULL,
    prep_ready_at TIMESTAMPTZ,
    locker_handoff_at TIMESTAMPTZ,
    picked_up_at TIMESTAMPTZ,
    metadata_json TEXT DEFAULT '{}' NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_opa_food_order ON food_delivery_orders (order_id);
CREATE INDEX IF NOT EXISTS idx_opa_food_platform ON food_delivery_orders (platform_code);
