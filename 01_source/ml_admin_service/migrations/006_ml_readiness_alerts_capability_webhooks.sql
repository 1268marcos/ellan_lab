-- Alertas de queda de score ML + webhooks por capability

CREATE TABLE IF NOT EXISTS ml_readiness_score_history (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    network_player_id VARCHAR(36) NOT NULL,
    network_player_code VARCHAR(48) NOT NULL,
    score_total NUMERIC(5, 2) NOT NULL,
    readiness_band VARCHAR(16) NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_ml_score_hist_player ON ml_readiness_score_history (network_player_id, recorded_at DESC);

CREATE TABLE IF NOT EXISTS ml_readiness_alerts (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    network_player_id VARCHAR(36) NOT NULL,
    network_player_code VARCHAR(48) NOT NULL,
    alert_type VARCHAR(32) NOT NULL DEFAULT 'SCORE_DROP',
    severity VARCHAR(16) NOT NULL DEFAULT 'WARNING',
    previous_score NUMERIC(5, 2),
    new_score NUMERIC(5, 2) NOT NULL,
    score_delta NUMERIC(5, 2) NOT NULL,
    previous_band VARCHAR(16),
    new_band VARCHAR(16) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'OPEN',
    webhook_dispatched BOOLEAN NOT NULL DEFAULT false,
    details_json TEXT NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    acknowledged_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_ml_readiness_alerts_open ON ml_readiness_alerts (status, created_at DESC);

CREATE TABLE IF NOT EXISTS ml_capability_webhooks (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    network_player_id VARCHAR(36) NOT NULL,
    network_player_code VARCHAR(48) NOT NULL,
    capability_code VARCHAR(40) NOT NULL,
    url VARCHAR(500) NOT NULL,
    secret_hash VARCHAR(128) NOT NULL,
    secret_key VARCHAR(256),
    event_types_json TEXT NOT NULL DEFAULT '["readiness.score_drop","telemetry.alert"]',
    active BOOLEAN NOT NULL DEFAULT true,
    last_http_status INTEGER,
    last_delivered_at TIMESTAMPTZ,
    last_error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_ml_cap_webhook UNIQUE (network_player_id, capability_code)
);

CREATE TABLE IF NOT EXISTS ml_capability_webhook_deliveries (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    webhook_id VARCHAR(36) NOT NULL,
    event_type VARCHAR(48) NOT NULL,
    payload_json TEXT NOT NULL,
    http_status INTEGER,
    success BOOLEAN NOT NULL DEFAULT false,
    response_snippet TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
