-- BI efficiency: data quality, scheduled exports, anomalies, bookmarks, pipeline sync

CREATE TABLE IF NOT EXISTS bi_data_quality_checks (
    id VARCHAR(36) PRIMARY KEY,
    check_code VARCHAR(48) NOT NULL UNIQUE,
    target_object VARCHAR(120) NOT NULL,
    rule_type VARCHAR(32) NOT NULL DEFAULT 'NOT_NULL',
    severity VARCHAR(16) NOT NULL DEFAULT 'WARNING',
    last_status VARCHAR(16) NOT NULL DEFAULT 'UNKNOWN',
    last_score NUMERIC(5, 2),
    last_run_at TIMESTAMPTZ,
    details_json TEXT NOT NULL DEFAULT '{}',
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS bi_scheduled_exports (
    id VARCHAR(36) PRIMARY KEY,
    schedule_code VARCHAR(48) NOT NULL UNIQUE,
    dataset_code VARCHAR(48) NOT NULL,
    cron_expr VARCHAR(64) NOT NULL DEFAULT '0 6 * * *',
    export_format VARCHAR(16) NOT NULL DEFAULT 'CSV',
    partner_id VARCHAR(36),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    last_run_at TIMESTAMPTZ,
    last_status VARCHAR(20) NOT NULL DEFAULT 'IDLE',
    next_run_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS bi_anomaly_signals (
    id VARCHAR(36) PRIMARY KEY,
    signal_type VARCHAR(32) NOT NULL,
    kpi_code VARCHAR(48),
    network_player_code VARCHAR(48),
    observed_value NUMERIC(18, 4),
    baseline_value NUMERIC(18, 4),
    deviation_pct NUMERIC(8, 3),
    severity VARCHAR(16) NOT NULL DEFAULT 'WARNING',
    status VARCHAR(20) NOT NULL DEFAULT 'OPEN',
    summary VARCHAR(255) NOT NULL,
    detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS bi_ops_bookmarks (
    id VARCHAR(36) PRIMARY KEY,
    owner_id VARCHAR(64) NOT NULL DEFAULT 'ops-default',
    label VARCHAR(120) NOT NULL,
    route_path VARCHAR(255) NOT NULL,
    query_json TEXT NOT NULL DEFAULT '{}',
    pinned BOOLEAN NOT NULL DEFAULT FALSE,
    sort_order INTEGER NOT NULL DEFAULT 100,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS bi_pipeline_sync_checkpoints (
    id VARCHAR(36) PRIMARY KEY,
    pipeline_code VARCHAR(48) NOT NULL UNIQUE,
    source_object VARCHAR(120) NOT NULL,
    target_object VARCHAR(120) NOT NULL,
    lag_minutes INTEGER NOT NULL DEFAULT 0,
    rows_synced BIGINT,
    status VARCHAR(20) NOT NULL DEFAULT 'OK',
    last_sync_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_bi_anomaly_status ON bi_anomaly_signals(status);
CREATE INDEX IF NOT EXISTS idx_bi_scheduled_exports_next ON bi_scheduled_exports(next_run_at);
