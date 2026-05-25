CREATE TABLE IF NOT EXISTS allocations (
    id VARCHAR(64) PRIMARY KEY,
    order_id VARCHAR(64) NOT NULL,
    locker_id VARCHAR(120),
    slot INTEGER NOT NULL,
    state VARCHAR(40) NOT NULL,
    locked_until TIMESTAMPTZ,
    allocated_at TIMESTAMPTZ,
    released_at TIMESTAMPTZ,
    release_reason VARCHAR(255),
    slot_size VARCHAR(20),
    ttl_seconds INTEGER,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_opa_allocations_order ON allocations (order_id);

CREATE TABLE IF NOT EXISTS logistics_manifests (
    id VARCHAR(36) PRIMARY KEY,
    logistics_partner_id VARCHAR(36) NOT NULL,
    locker_id VARCHAR(64) NOT NULL,
    manifest_date DATE NOT NULL,
    carrier_route_code VARCHAR(64),
    carrier_vehicle_id VARCHAR(64),
    expected_parcel_count INTEGER DEFAULT 0 NOT NULL,
    actual_parcel_count INTEGER DEFAULT 0 NOT NULL,
    status VARCHAR(20) DEFAULT 'PENDING' NOT NULL,
    dispatched_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    carrier_note TEXT,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS logistics_manifest_items (
    id VARCHAR(36) PRIMARY KEY,
    manifest_id VARCHAR(36) NOT NULL,
    delivery_id VARCHAR(36),
    tracking_code VARCHAR(128) NOT NULL,
    sequence_number INTEGER,
    status VARCHAR(20) DEFAULT 'EXPECTED' NOT NULL,
    exception_note TEXT,
    processed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_opa_manifest_items_manifest ON logistics_manifest_items (manifest_id);

CREATE TABLE IF NOT EXISTS order_integration_channels (
    id VARCHAR(36) PRIMARY KEY,
    code VARCHAR(32) NOT NULL UNIQUE,
    name VARCHAR(128) NOT NULL,
    player_type VARCHAR(30) NOT NULL,
    country VARCHAR(2) DEFAULT 'BR' NOT NULL,
    region_scope VARCHAR(20) DEFAULT 'LOCAL' NOT NULL,
    api_profile VARCHAR(50),
    active BOOLEAN DEFAULT true NOT NULL,
    metadata_json TEXT DEFAULT '{}' NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS order_marketplace_commissions (
    id VARCHAR(36) PRIMARY KEY,
    seller_id VARCHAR(36) NOT NULL,
    order_id VARCHAR(64) NOT NULL,
    order_item_id VARCHAR(36),
    commission_rate_pct NUMERIC(5,2) NOT NULL,
    commission_amount_cents INTEGER NOT NULL,
    ellan_fee_cents INTEGER NOT NULL,
    payment_gateway_fee_cents INTEGER DEFAULT 0 NOT NULL,
    net_to_seller_cents INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'PENDING' NOT NULL,
    settled_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_opa_mc_order ON order_marketplace_commissions (order_id);

CREATE TABLE IF NOT EXISTS lifecycle_deadlines (
    id VARCHAR(36) PRIMARY KEY,
    deadline_key VARCHAR(200) NOT NULL UNIQUE,
    order_id VARCHAR(100) NOT NULL,
    order_channel VARCHAR(50),
    deadline_type VARCHAR(50) NOT NULL,
    status VARCHAR(30) NOT NULL,
    due_at TIMESTAMPTZ NOT NULL,
    failure_count INTEGER DEFAULT 0 NOT NULL,
    payload_json TEXT DEFAULT '{}' NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_opa_ld_order ON lifecycle_deadlines (order_id);

CREATE TABLE IF NOT EXISTS order_ops_audit (
    id VARCHAR(40) PRIMARY KEY,
    action VARCHAR(120) NOT NULL,
    result VARCHAR(20) NOT NULL,
    correlation_id VARCHAR(80) NOT NULL,
    order_id VARCHAR(64),
    user_id VARCHAR(36),
    role VARCHAR(80),
    error_message TEXT,
    details_json TEXT DEFAULT '{}' NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_opa_audit_order ON order_ops_audit (order_id);
