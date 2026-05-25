-- hardware_admin_service DDL (aligned to complete_schema_20260524_a.sql subset)

CREATE TABLE IF NOT EXISTS hardware_vendor_partners (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    code VARCHAR(32) NOT NULL UNIQUE,
    vendor_type VARCHAR(30) NOT NULL,
    region_code VARCHAR(20),
    api_base_url VARCHAR(500),
    credentials_secret_ref VARCHAR(255),
    webhook_secret_ref VARCHAR(255),
    country VARCHAR(2) DEFAULT 'BR' NOT NULL,
    active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS hardware_vendor_webhook_endpoints (
    id VARCHAR(36) PRIMARY KEY,
    vendor_id VARCHAR(36) NOT NULL,
    url VARCHAR(500) NOT NULL,
    secret_hash VARCHAR(128) NOT NULL,
    secret_key VARCHAR(256),
    events_json TEXT DEFAULT '["locker.*","telemetry.*"]' NOT NULL,
    api_version VARCHAR(10) DEFAULT 'v1' NOT NULL,
    retry_policy TEXT DEFAULT '{}' NOT NULL,
    active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS hardware_vendor_api_keys (
    id VARCHAR(36) PRIMARY KEY,
    vendor_id VARCHAR(36) NOT NULL,
    key_prefix VARCHAR(16) NOT NULL,
    key_hash VARCHAR(128) NOT NULL,
    label VARCHAR(64),
    scopes_json TEXT DEFAULT '["hardware:write","telemetry:read"]' NOT NULL,
    expires_at TIMESTAMPTZ,
    last_used_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    created_by VARCHAR(36),
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS hardware_assets (
    id VARCHAR(36) PRIMARY KEY,
    asset_code VARCHAR(64) NOT NULL UNIQUE,
    locker_id VARCHAR(36),
    partner_id VARCHAR(36),
    vendor_id VARCHAR(36),
    asset_category VARCHAR(40) NOT NULL,
    description VARCHAR(255) NOT NULL,
    acquisition_date DATE NOT NULL,
    in_service_date DATE,
    acquisition_cost_cents BIGINT NOT NULL,
    installation_cost_cents BIGINT DEFAULT 0 NOT NULL,
    residual_value_cents BIGINT DEFAULT 0 NOT NULL,
    useful_life_months INTEGER NOT NULL,
    depreciation_method VARCHAR(20) DEFAULT 'STRAIGHT_LINE' NOT NULL,
    currency VARCHAR(8) DEFAULT 'BRL' NOT NULL,
    country_code VARCHAR(2),
    jurisdiction_code VARCHAR(32),
    supplier_name VARCHAR(140),
    warranty_ends_at DATE,
    status VARCHAR(20) DEFAULT 'ACTIVE' NOT NULL,
    notes TEXT,
    metadata_json JSONB DEFAULT '{}'::jsonb NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS locker_operators_admin (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    document VARCHAR(32),
    email VARCHAR(128),
    phone VARCHAR(32),
    operator_type VARCHAR(32) DEFAULT 'LOGISTICS' NOT NULL,
    country VARCHAR(2) DEFAULT 'BR' NOT NULL,
    active BOOLEAN DEFAULT true NOT NULL,
    commission_rate DOUBLE PRECISION,
    currency VARCHAR(8) DEFAULT 'BRL' NOT NULL,
    contract_ref VARCHAR(255),
    sla_pickup_hours INTEGER DEFAULT 72 NOT NULL,
    sla_return_hours INTEGER DEFAULT 24 NOT NULL,
    status VARCHAR(30) DEFAULT 'DRAFT' NOT NULL,
    legal_name VARCHAR(140),
    tier VARCHAR(20) DEFAULT 'STANDARD' NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS runtime_lockers_admin (
    locker_id VARCHAR(120) PRIMARY KEY,
    machine_id VARCHAR(120) NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    region VARCHAR(16) NOT NULL,
    country VARCHAR(8) NOT NULL,
    timezone VARCHAR(64) NOT NULL,
    operator_id VARCHAR(120),
    vendor_id VARCHAR(36),
    temperature_zone VARCHAR(32) DEFAULT 'AMBIENT' NOT NULL,
    security_level VARCHAR(32) DEFAULT 'STANDARD' NOT NULL,
    active BOOLEAN DEFAULT true NOT NULL,
    runtime_enabled BOOLEAN DEFAULT true NOT NULL,
    mqtt_region VARCHAR(32) NOT NULL,
    mqtt_locker_id VARCHAR(120) NOT NULL,
    topology_version INTEGER DEFAULT 1 NOT NULL,
    slot_count_total INTEGER NOT NULL,
    payment_methods_json JSONB DEFAULT '[]'::jsonb NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS hardware_device_registry (
    device_hash VARCHAR(128) PRIMARY KEY,
    version VARCHAR(32) NOT NULL,
    first_seen_at_epoch BIGINT NOT NULL,
    last_seen_at_epoch BIGINT NOT NULL,
    seen_count INTEGER DEFAULT 1 NOT NULL,
    locker_id VARCHAR(120),
    vendor_id VARCHAR(36),
    region_code VARCHAR(20),
    flags_json JSONB DEFAULT '{}'::jsonb NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS hardware_sync_queue (
    id VARCHAR(36) PRIMARY KEY,
    locker_id VARCHAR(64) NOT NULL,
    operation VARCHAR(32) NOT NULL,
    status VARCHAR(20) NOT NULL,
    retry_count INTEGER DEFAULT 0 NOT NULL,
    max_retries INTEGER DEFAULT 3 NOT NULL,
    last_error TEXT,
    processed_at TIMESTAMPTZ,
    next_retry_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS hardware_telemetry_events (
    id VARCHAR(36) PRIMARY KEY,
    locker_id VARCHAR(120) NOT NULL,
    event_type VARCHAR(64) NOT NULL,
    severity VARCHAR(20) DEFAULT 'INFO' NOT NULL,
    slot_number INTEGER,
    payload_json JSONB DEFAULT '{}'::jsonb NOT NULL,
    created_at_epoch BIGINT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);
