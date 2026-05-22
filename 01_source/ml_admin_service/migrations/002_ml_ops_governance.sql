-- ML Ops profissional: catalogo de casos de uso, registry, experimentos, drift, SLO e deployments

CREATE TABLE IF NOT EXISTS ml_use_cases (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    code VARCHAR(48) NOT NULL UNIQUE,
    name VARCHAR(140) NOT NULL,
    domain VARCHAR(32) NOT NULL DEFAULT 'LOCKER',
    description TEXT,
    owner_team VARCHAR(64),
    tier VARCHAR(20) NOT NULL DEFAULT 'STANDARD',
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ml_model_registry (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    use_case_id VARCHAR(36) NOT NULL REFERENCES ml_use_cases(id) ON DELETE CASCADE,
    model_version VARCHAR(64) NOT NULL,
    algorithm VARCHAR(64) NOT NULL DEFAULT 'RandomForest',
    framework VARCHAR(32) DEFAULT 'sklearn',
    artifact_uri VARCHAR(500),
    stage VARCHAR(20) NOT NULL DEFAULT 'DEV',
    status_note VARCHAR(255),
    registry_metadata_json TEXT NOT NULL DEFAULT '{}',
    promoted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_ml_registry_use_case_version UNIQUE (use_case_id, model_version)
);

CREATE INDEX IF NOT EXISTS ix_ml_model_registry_stage ON ml_model_registry (stage);
CREATE INDEX IF NOT EXISTS ix_ml_model_registry_use_case ON ml_model_registry (use_case_id);

CREATE TABLE IF NOT EXISTS ml_training_runs (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    use_case_id VARCHAR(36) NOT NULL REFERENCES ml_use_cases(id) ON DELETE CASCADE,
    run_name VARCHAR(120) NOT NULL,
    model_version VARCHAR(64),
    status VARCHAR(20) NOT NULL DEFAULT 'QUEUED',
    triggered_by VARCHAR(64),
    dataset_ref VARCHAR(255),
    hyperparams_json TEXT NOT NULL DEFAULT '{}',
    metrics_json TEXT NOT NULL DEFAULT '{}',
    error_message TEXT,
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_ml_training_runs_use_case ON ml_training_runs (use_case_id, status);

CREATE TABLE IF NOT EXISTS ml_feature_definitions (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    use_case_id VARCHAR(36) REFERENCES ml_use_cases(id) ON DELETE SET NULL,
    feature_name VARCHAR(80) NOT NULL,
    feature_group VARCHAR(40) NOT NULL DEFAULT 'telemetry',
    data_type VARCHAR(24) NOT NULL DEFAULT 'float',
    source_table VARCHAR(80),
    freshness_hours INTEGER NOT NULL DEFAULT 24,
    is_nullable BOOLEAN NOT NULL DEFAULT true,
    description TEXT,
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_ml_feature_def_name UNIQUE (feature_name)
);

CREATE TABLE IF NOT EXISTS ml_drift_reports (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    use_case_id VARCHAR(36) NOT NULL REFERENCES ml_use_cases(id) ON DELETE CASCADE,
    model_version VARCHAR(64) NOT NULL,
    report_date DATE NOT NULL DEFAULT CURRENT_DATE,
    drift_type VARCHAR(24) NOT NULL DEFAULT 'DATA',
    psi_score NUMERIC(6, 4),
    status VARCHAR(20) NOT NULL DEFAULT 'OK',
    details_json TEXT NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_ml_drift_reports_use_case ON ml_drift_reports (use_case_id, report_date DESC);

CREATE TABLE IF NOT EXISTS ml_inference_slo (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    use_case_id VARCHAR(36) NOT NULL UNIQUE REFERENCES ml_use_cases(id) ON DELETE CASCADE,
    p95_latency_ms INTEGER NOT NULL DEFAULT 500,
    min_availability_pct NUMERIC(5, 2) NOT NULL DEFAULT 99.50,
    max_error_rate_pct NUMERIC(5, 2) NOT NULL DEFAULT 1.00,
    min_predictions_per_day INTEGER NOT NULL DEFAULT 100,
    active BOOLEAN NOT NULL DEFAULT true,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ml_alert_rules (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    use_case_id VARCHAR(36) NOT NULL REFERENCES ml_use_cases(id) ON DELETE CASCADE,
    rule_code VARCHAR(48) NOT NULL,
    metric VARCHAR(64) NOT NULL,
    operator VARCHAR(8) NOT NULL DEFAULT 'GT',
    threshold NUMERIC(12, 4) NOT NULL,
    severity VARCHAR(16) NOT NULL DEFAULT 'WARNING',
    notify_webhook BOOLEAN NOT NULL DEFAULT true,
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_ml_alert_rule_code UNIQUE (use_case_id, rule_code)
);

CREATE TABLE IF NOT EXISTS ml_deployment_events (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    use_case_id VARCHAR(36) NOT NULL REFERENCES ml_use_cases(id) ON DELETE CASCADE,
    from_version VARCHAR(64),
    to_version VARCHAR(64) NOT NULL,
    event_type VARCHAR(24) NOT NULL DEFAULT 'PROMOTE',
    actor_id VARCHAR(64),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_ml_deployment_events_use_case ON ml_deployment_events (use_case_id, created_at DESC);

CREATE TABLE IF NOT EXISTS ml_partner_use_case_grants (
    partner_id VARCHAR(36) NOT NULL REFERENCES ml_data_partners(id) ON DELETE CASCADE,
    use_case_id VARCHAR(36) NOT NULL REFERENCES ml_use_cases(id) ON DELETE CASCADE,
    scopes_json TEXT NOT NULL DEFAULT '["ml:predict","ml:read"]',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (partner_id, use_case_id)
);
