-- Webhooks por capability (espelho marketplace + ingress Ellan)

CREATE TABLE IF NOT EXISTS partner_capability_webhooks (
    id VARCHAR(36) PRIMARY KEY,
    ecosystem_player_id VARCHAR(36) NOT NULL,
    player_code VARCHAR(48) NOT NULL,
    capability_code VARCHAR(40) NOT NULL,
    url VARCHAR(500) NOT NULL,
    secret_hash VARCHAR(128) NOT NULL,
    secret_key VARCHAR(256),
    event_types_json TEXT NOT NULL DEFAULT '["capability.health","webhook.test"]',
    source VARCHAR(32) NOT NULL DEFAULT 'SEED',
    marketplace_webhook_id VARCHAR(36),
    active BOOLEAN NOT NULL DEFAULT 1,
    last_http_status INTEGER,
    last_delivered_at TIMESTAMP,
    last_error TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ecosystem_player_id) REFERENCES partner_ecosystem_players(id) ON DELETE CASCADE,
    UNIQUE (ecosystem_player_id, capability_code)
);

CREATE INDEX IF NOT EXISTS ix_partner_cap_webhook_player ON partner_capability_webhooks(ecosystem_player_id, active);

CREATE TABLE IF NOT EXISTS partner_capability_webhook_deliveries (
    id VARCHAR(36) PRIMARY KEY,
    webhook_id VARCHAR(36) NOT NULL,
    event_type VARCHAR(48) NOT NULL,
    payload_json TEXT NOT NULL,
    http_status INTEGER,
    success BOOLEAN NOT NULL DEFAULT 0,
    response_snippet TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (webhook_id) REFERENCES partner_capability_webhooks(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_partner_cap_wh_del ON partner_capability_webhook_deliveries(webhook_id);
