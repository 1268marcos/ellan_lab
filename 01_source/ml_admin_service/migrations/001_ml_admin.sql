-- DDL alinhado a complete_schema_20260522_A.sql (tabelas ML core + admin parceiros ML)

CREATE TABLE IF NOT EXISTS ml_data_partners (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    code VARCHAR(32) NOT NULL UNIQUE,
    partner_type VARCHAR(30) NOT NULL DEFAULT 'TELEMETRY',
    region_code VARCHAR(20),
    api_base_url VARCHAR(500),
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ml_partner_webhook_endpoints (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    partner_id VARCHAR(36) NOT NULL,
    url VARCHAR(500) NOT NULL,
    secret_hash VARCHAR(128) NOT NULL,
    secret_key VARCHAR(256),
    events_json TEXT NOT NULL DEFAULT '["prediction.*","feedback.*"]',
    api_version VARCHAR(10) NOT NULL DEFAULT 'v1',
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_ml_partner_webhook_partner ON ml_partner_webhook_endpoints (partner_id);

CREATE TABLE IF NOT EXISTS ml_partner_api_keys (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    partner_id VARCHAR(36) NOT NULL,
    key_prefix VARCHAR(16) NOT NULL,
    key_hash VARCHAR(128) NOT NULL,
    label VARCHAR(64),
    scopes_json TEXT NOT NULL DEFAULT '["ml:read","ml:write"]',
    expires_at TIMESTAMPTZ,
    last_used_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    created_by VARCHAR(36),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_ml_partner_api_keys_partner ON ml_partner_api_keys (partner_id);
