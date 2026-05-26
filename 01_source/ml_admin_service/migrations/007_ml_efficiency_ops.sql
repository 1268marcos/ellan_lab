-- ML efficiency: inference usage, feature freshness breaches, OPS recommendations

CREATE TABLE IF NOT EXISTS ml_inference_usage_daily (
    id VARCHAR(36) PRIMARY KEY,
    usage_date DATE NOT NULL,
    use_case_code VARCHAR(48) NOT NULL,
    network_player_code VARCHAR(48),
    request_count BIGINT NOT NULL DEFAULT 0,
    p95_latency_ms INTEGER,
    error_rate_pct NUMERIC(6, 3),
    estimated_cost_usd NUMERIC(12, 4),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ml_feature_freshness_breaches (
    id VARCHAR(36) PRIMARY KEY,
    feature_name VARCHAR(64) NOT NULL,
    source_table VARCHAR(120) NOT NULL,
    sla_hours INTEGER NOT NULL DEFAULT 24,
    lag_hours NUMERIC(8, 2) NOT NULL,
    severity VARCHAR(16) NOT NULL DEFAULT 'WARNING',
    status VARCHAR(20) NOT NULL DEFAULT 'OPEN',
    summary VARCHAR(255) NOT NULL,
    detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS ml_ops_recommendations (
    id VARCHAR(36) PRIMARY KEY,
    recommendation_code VARCHAR(48) NOT NULL,
    category VARCHAR(32) NOT NULL DEFAULT 'EFFICIENCY',
    priority VARCHAR(16) NOT NULL DEFAULT 'MEDIUM',
    title VARCHAR(160) NOT NULL,
    action_hint TEXT NOT NULL,
    related_entity VARCHAR(64),
    status VARCHAR(20) NOT NULL DEFAULT 'OPEN',
    impact_score NUMERIC(5, 2) NOT NULL DEFAULT 50,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    dismissed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_ml_inference_usage_date ON ml_inference_usage_daily(usage_date);
CREATE INDEX IF NOT EXISTS idx_ml_freshness_status ON ml_feature_freshness_breaches(status);
CREATE INDEX IF NOT EXISTS idx_ml_ops_rec_status ON ml_ops_recommendations(status);
