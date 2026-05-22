-- Prontidao de integracao ML (espelho marketplace + telemetria)

CREATE TABLE IF NOT EXISTS ml_integration_readiness_snapshots (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    network_player_id VARCHAR(36) NOT NULL REFERENCES ml_locker_network_players(id) ON DELETE CASCADE,
    network_player_code VARCHAR(48) NOT NULL,
    marketplace_channel_id VARCHAR(36),
    score_total NUMERIC(5, 2) NOT NULL DEFAULT 0,
    score_capabilities NUMERIC(5, 2) NOT NULL DEFAULT 0,
    score_telemetry NUMERIC(5, 2) NOT NULL DEFAULT 0,
    score_ml_ops NUMERIC(5, 2) NOT NULL DEFAULT 0,
    readiness_band VARCHAR(16) NOT NULL DEFAULT 'PLANNED',
    blockers_json TEXT NOT NULL DEFAULT '[]',
    factors_json TEXT NOT NULL DEFAULT '{}',
    computed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_ml_readiness_network UNIQUE (network_player_id)
);

CREATE INDEX IF NOT EXISTS ix_ml_readiness_band ON ml_integration_readiness_snapshots (readiness_band, score_total DESC);

CREATE TABLE IF NOT EXISTS ml_ops_audit_log (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    event_type VARCHAR(40) NOT NULL,
    entity_type VARCHAR(32) NOT NULL,
    entity_id VARCHAR(48),
    summary VARCHAR(255) NOT NULL,
    payload_json TEXT NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_ml_ops_audit_created ON ml_ops_audit_log (created_at DESC);
