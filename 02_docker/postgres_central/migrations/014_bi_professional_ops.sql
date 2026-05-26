-- BI / Analytics professional ops (readiness, marts refresh, alerts, lineage, exports)

CREATE TABLE IF NOT EXISTS bi_player_segment_taxonomy (
    code VARCHAR(32) NOT NULL PRIMARY KEY,
    label VARCHAR(120) NOT NULL,
    description TEXT,
    sort_order INTEGER NOT NULL DEFAULT 100,
    active BOOLEAN NOT NULL DEFAULT true
);

CREATE TABLE IF NOT EXISTS bi_player_market_presence (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    network_player_code VARCHAR(48) NOT NULL,
    country_code VARCHAR(2) NOT NULL,
    region_code VARCHAR(20),
    locker_count_est INTEGER,
    parcel_volume_est_monthly BIGINT,
    market_share_pct NUMERIC(6,3),
    active BOOLEAN NOT NULL DEFAULT true,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_bi_market_presence_player ON bi_player_market_presence (network_player_code, country_code);

CREATE TABLE IF NOT EXISTS bi_data_readiness_snapshots (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    network_player_code VARCHAR(48) NOT NULL,
    segment_code VARCHAR(32) NOT NULL DEFAULT 'LOCKER_NETWORK',
    score_total NUMERIC(5,2) NOT NULL DEFAULT 0,
    score_data_quality NUMERIC(5,2) NOT NULL DEFAULT 0,
    score_mart_freshness NUMERIC(5,2) NOT NULL DEFAULT 0,
    score_api_coverage NUMERIC(5,2) NOT NULL DEFAULT 0,
    readiness_band VARCHAR(16) NOT NULL DEFAULT 'PLANNED',
    blockers_json TEXT NOT NULL DEFAULT '[]',
    factors_json TEXT NOT NULL DEFAULT '{}',
    computed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_bi_readiness_player UNIQUE (network_player_code)
);

CREATE INDEX IF NOT EXISTS ix_bi_readiness_band ON bi_data_readiness_snapshots (readiness_band, score_total DESC);

CREATE TABLE IF NOT EXISTS bi_mart_refresh_jobs (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    mart_name VARCHAR(64) NOT NULL,
    target_schema VARCHAR(64) NOT NULL DEFAULT 'analytics_analytics',
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    rows_affected BIGINT,
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    error_message TEXT,
    triggered_by VARCHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_bi_mart_refresh_status ON bi_mart_refresh_jobs (status, created_at DESC);

CREATE TABLE IF NOT EXISTS bi_kpi_alert_rules (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    kpi_code VARCHAR(48) NOT NULL,
    comparator VARCHAR(8) NOT NULL DEFAULT 'LT',
    threshold_value NUMERIC(18,4) NOT NULL,
    severity VARCHAR(16) NOT NULL DEFAULT 'WARNING',
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS bi_kpi_alert_events (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    rule_id VARCHAR(36) NOT NULL REFERENCES bi_kpi_alert_rules(id) ON DELETE CASCADE,
    kpi_code VARCHAR(48) NOT NULL,
    observed_value NUMERIC(18,4) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'OPEN',
    network_player_code VARCHAR(48),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_bi_kpi_alert_open ON bi_kpi_alert_events (status, created_at DESC);

CREATE TABLE IF NOT EXISTS bi_data_lineage_edges (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    source_object VARCHAR(120) NOT NULL,
    target_object VARCHAR(120) NOT NULL,
    transform_type VARCHAR(32) NOT NULL DEFAULT 'DBT_MODEL',
    owner_team VARCHAR(64) NOT NULL DEFAULT 'data-platform',
    notes TEXT,
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS bi_export_jobs (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    partner_id VARCHAR(36),
    export_format VARCHAR(16) NOT NULL DEFAULT 'CSV',
    dataset_code VARCHAR(48) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'QUEUED',
    file_url VARCHAR(500),
    row_count BIGINT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS bi_ops_audit_log (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    event_type VARCHAR(40) NOT NULL,
    entity_type VARCHAR(32) NOT NULL,
    entity_id VARCHAR(48),
    summary VARCHAR(255) NOT NULL,
    payload_json TEXT NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_bi_ops_audit_created ON bi_ops_audit_log (created_at DESC);

CREATE TABLE IF NOT EXISTS bi_unified_domain_links (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    domain_code VARCHAR(24) NOT NULL,
    label VARCHAR(120) NOT NULL,
    admin_route VARCHAR(255),
    health_path VARCHAR(255),
    sort_order INTEGER NOT NULL DEFAULT 100,
    active BOOLEAN NOT NULL DEFAULT true
);
