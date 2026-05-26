-- Admin tables for BI / Analytics (Ellan locker platform)

CREATE TABLE IF NOT EXISTS bi_data_partners (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    code VARCHAR(32) NOT NULL UNIQUE,
    partner_type VARCHAR(30) NOT NULL DEFAULT 'WAREHOUSE',
    region_code VARCHAR(20),
    api_base_url VARCHAR(500),
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS bi_partner_webhook_endpoints (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    partner_id VARCHAR(36) NOT NULL,
    url VARCHAR(500) NOT NULL,
    secret_hash VARCHAR(128) NOT NULL,
    secret_key VARCHAR(256),
    events_json TEXT NOT NULL DEFAULT '["fact.ingested","mart.refreshed"]',
    api_version VARCHAR(10) NOT NULL DEFAULT 'v1',
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_bi_partner_webhook_partner ON bi_partner_webhook_endpoints (partner_id);

CREATE TABLE IF NOT EXISTS bi_partner_api_keys (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    partner_id VARCHAR(36) NOT NULL,
    key_prefix VARCHAR(16) NOT NULL,
    key_hash VARCHAR(128) NOT NULL,
    label VARCHAR(64),
    scopes_json TEXT NOT NULL DEFAULT '["bi:read","bi:write","analytics:export"]',
    expires_at TIMESTAMPTZ,
    last_used_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    created_by VARCHAR(36),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS bi_api_key_rotation_log (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    partner_id VARCHAR(36) NOT NULL,
    old_key_prefix VARCHAR(16),
    new_key_prefix VARCHAR(16) NOT NULL,
    rotated_by VARCHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS bi_kpi_definitions (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    code VARCHAR(48) NOT NULL UNIQUE,
    name VARCHAR(160) NOT NULL,
    domain VARCHAR(32) NOT NULL DEFAULT 'LOCKER',
    grain VARCHAR(24) NOT NULL DEFAULT 'DAILY',
    source_table VARCHAR(80) NOT NULL,
    formula_hint TEXT,
    owner_team VARCHAR(64) NOT NULL DEFAULT 'data-platform',
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS bi_report_catalog (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    code VARCHAR(48) NOT NULL UNIQUE,
    name VARCHAR(160) NOT NULL,
    report_type VARCHAR(24) NOT NULL DEFAULT 'DASHBOARD',
    metabase_dashboard_id VARCHAR(36),
    description TEXT,
    tags_json TEXT NOT NULL DEFAULT '["ops","locker"]',
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS bi_locker_network_players (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    code VARCHAR(48) NOT NULL UNIQUE,
    name VARCHAR(160) NOT NULL,
    player_role VARCHAR(32) NOT NULL DEFAULT 'LOCKER_NETWORK',
    parent_group VARCHAR(64) NOT NULL DEFAULT 'GLOBAL',
    country VARCHAR(2) NOT NULL DEFAULT 'BR',
    regions_json TEXT NOT NULL DEFAULT '["BR"]',
    supports_lockers BOOLEAN NOT NULL DEFAULT true,
    supports_marketplace BOOLEAN NOT NULL DEFAULT false,
    integration_mode VARCHAR(32) NOT NULL DEFAULT 'API',
    global_tier VARCHAR(16) NOT NULL DEFAULT 'TIER1',
    bi_priority_score NUMERIC(5,2) NOT NULL DEFAULT 50,
    sort_order INTEGER NOT NULL DEFAULT 100,
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS bi_player_relations (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    from_player_code VARCHAR(48) NOT NULL,
    to_player_code VARCHAR(48) NOT NULL,
    relation_type VARCHAR(32) NOT NULL DEFAULT 'DATA_SHARE',
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS bi_capability_webhooks (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    network_player_code VARCHAR(48) NOT NULL,
    capability_code VARCHAR(40) NOT NULL,
    url VARCHAR(500) NOT NULL,
    secret_hash VARCHAR(128) NOT NULL,
    secret_key VARCHAR(256),
    event_types_json TEXT NOT NULL DEFAULT '["mart.refreshed","kpi.threshold"]',
    active BOOLEAN NOT NULL DEFAULT true,
    last_http_status INTEGER,
    last_delivered_at TIMESTAMPTZ,
    last_error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_bi_capability_webhooks_player ON bi_capability_webhooks (network_player_code);
