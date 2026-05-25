-- Cross-domain hardware relations (marketplace, payment, carriers, finance, topology)

CREATE TABLE IF NOT EXISTS hardware_ecosystem_players (
    id VARCHAR(36) PRIMARY KEY,
    player_code VARCHAR(48) NOT NULL UNIQUE,
    name VARCHAR(160) NOT NULL,
    segment VARCHAR(32) NOT NULL,
    primary_country VARCHAR(2) NOT NULL,
    vendor_id VARCHAR(36),
    operator_id VARCHAR(64),
    marketplace_channel_code VARCHAR(48),
    ml_network_code VARCHAR(48),
    payment_provider_code VARCHAR(32),
    finance_catalog_code VARCHAR(48),
    fiscal_corridor_code VARCHAR(48),
    carrier_code VARCHAR(32),
    regions_json JSONB DEFAULT '[]'::jsonb NOT NULL,
    metadata_json JSONB DEFAULT '{}'::jsonb NOT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS hardware_locker_marketplace_links (
    id VARCHAR(36) PRIMARY KEY,
    seller_id VARCHAR(36) NOT NULL,
    seller_name VARCHAR(128),
    channel_partner_id VARCHAR(36) NOT NULL,
    channel_code VARCHAR(48) NOT NULL,
    channel_name VARCHAR(128),
    locker_id VARCHAR(120),
    vendor_id VARCHAR(36),
    priority INTEGER DEFAULT 100 NOT NULL,
    active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS hardware_locker_payment_bindings (
    id VARCHAR(36) PRIMARY KEY,
    locker_id VARCHAR(120) NOT NULL,
    payment_method_code VARCHAR(80) NOT NULL,
    payment_provider_code VARCHAR(32),
    payment_interface_code VARCHAR(80),
    is_active BOOLEAN DEFAULT true NOT NULL,
    priority INTEGER DEFAULT 100 NOT NULL,
    metadata_json JSONB DEFAULT '{}'::jsonb NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS hardware_locker_carrier_bindings (
    id VARCHAR(36) PRIMARY KEY,
    locker_id VARCHAR(120) NOT NULL,
    carrier_code VARCHAR(32) NOT NULL,
    carrier_name VARCHAR(128) NOT NULL,
    service_level VARCHAR(32) DEFAULT 'STANDARD' NOT NULL,
    country_code VARCHAR(2) NOT NULL,
    operator_id VARCHAR(64),
    tracking_prefix VARCHAR(16),
    is_active BOOLEAN DEFAULT true NOT NULL,
    metadata_json JSONB DEFAULT '{}'::jsonb NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS hardware_domain_references (
    id VARCHAR(36) PRIMARY KEY,
    locker_id VARCHAR(120) NOT NULL,
    domain_type VARCHAR(32) NOT NULL,
    external_id VARCHAR(120) NOT NULL,
    external_code VARCHAR(64),
    relation_type VARCHAR(32) DEFAULT 'LINK' NOT NULL,
    notes TEXT,
    metadata_json JSONB DEFAULT '{}'::jsonb NOT NULL,
    active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS hardware_locker_capex (
    id VARCHAR(36) PRIMARY KEY,
    locker_id VARCHAR(120) NOT NULL,
    asset_id VARCHAR(36),
    acquisition_cost_cents BIGINT NOT NULL,
    installation_cost_cents BIGINT DEFAULT 0 NOT NULL,
    equipment_cost_cents BIGINT DEFAULT 0 NOT NULL,
    connectivity_setup_cents BIGINT DEFAULT 0 NOT NULL,
    residual_value_cents BIGINT DEFAULT 0 NOT NULL,
    useful_life_months INTEGER DEFAULT 60 NOT NULL,
    depreciation_method VARCHAR(20) DEFAULT 'STRAIGHT_LINE' NOT NULL,
    depreciation_start_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'ACTIVE' NOT NULL,
    supplier VARCHAR(255),
    metadata_json JSONB DEFAULT '{}'::jsonb NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS hardware_locker_opex (
    id VARCHAR(36) PRIMARY KEY,
    locker_id VARCHAR(120) NOT NULL,
    reference_month DATE NOT NULL,
    cost_type VARCHAR(40) NOT NULL,
    amount_cents BIGINT NOT NULL,
    currency VARCHAR(8) DEFAULT 'BRL' NOT NULL,
    description TEXT,
    invoice_ref VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS hardware_locker_features (
    locker_id VARCHAR(120) PRIMARY KEY,
    supports_kiosk BOOLEAN DEFAULT true NOT NULL,
    supports_ble BOOLEAN DEFAULT false NOT NULL,
    supports_nfc BOOLEAN DEFAULT false NOT NULL,
    supports_printer BOOLEAN DEFAULT false NOT NULL,
    supports_card_reader BOOLEAN DEFAULT false NOT NULL,
    supports_open_command BOOLEAN DEFAULT true NOT NULL,
    supports_light_command BOOLEAN DEFAULT true NOT NULL,
    supports_refrigerated BOOLEAN DEFAULT false NOT NULL,
    supports_high_value BOOLEAN DEFAULT false NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS hardware_locker_slots (
    id VARCHAR(36) PRIMARY KEY,
    locker_id VARCHAR(120) NOT NULL,
    slot_number INTEGER NOT NULL,
    slot_size VARCHAR(16) NOT NULL,
    width_mm INTEGER,
    height_mm INTEGER,
    depth_mm INTEGER,
    max_weight_g INTEGER,
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_hw_mkt_link_locker ON hardware_locker_marketplace_links (locker_id, active);
CREATE INDEX IF NOT EXISTS ix_hw_pay_binding_locker ON hardware_locker_payment_bindings (locker_id, is_active);
CREATE INDEX IF NOT EXISTS ix_hw_carrier_locker ON hardware_locker_carrier_bindings (locker_id, carrier_code);
CREATE INDEX IF NOT EXISTS ix_hw_domain_ref ON hardware_domain_references (locker_id, domain_type);
