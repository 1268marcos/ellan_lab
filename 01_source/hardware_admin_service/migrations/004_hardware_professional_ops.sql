-- Professional / world-class hardware ops layer

CREATE TABLE IF NOT EXISTS hardware_integration_readiness (
    player_id VARCHAR(36) PRIMARY KEY,
    player_code VARCHAR(48) NOT NULL,
    score_total NUMERIC(5, 2) DEFAULT 0 NOT NULL,
    score_capabilities NUMERIC(5, 2) DEFAULT 0 NOT NULL,
    score_api NUMERIC(5, 2) DEFAULT 0 NOT NULL,
    score_operations NUMERIC(5, 2) DEFAULT 0 NOT NULL,
    readiness_band VARCHAR(16) DEFAULT 'PLANNED' NOT NULL,
    blockers_json JSONB DEFAULT '[]'::jsonb NOT NULL,
    marketplace_partner_code VARCHAR(48),
    computed_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_hw_readiness_band ON hardware_integration_readiness (readiness_band);

CREATE TABLE IF NOT EXISTS hardware_readiness_alerts (
    id VARCHAR(36) PRIMARY KEY,
    player_id VARCHAR(36) NOT NULL,
    player_code VARCHAR(48) NOT NULL,
    alert_type VARCHAR(32) NOT NULL,
    severity VARCHAR(16) DEFAULT 'WARNING' NOT NULL,
    previous_score NUMERIC(5, 2),
    new_score NUMERIC(5, 2) NOT NULL,
    score_delta NUMERIC(5, 2) DEFAULT 0 NOT NULL,
    previous_band VARCHAR(16),
    new_band VARCHAR(16) NOT NULL,
    status VARCHAR(16) DEFAULT 'OPEN' NOT NULL,
    webhook_dispatched BOOLEAN DEFAULT false NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS hardware_integration_incidents (
    id VARCHAR(36) PRIMARY KEY,
    player_id VARCHAR(36),
    player_code VARCHAR(48),
    locker_id VARCHAR(120),
    severity VARCHAR(16) DEFAULT 'WARNING' NOT NULL,
    incident_type VARCHAR(32) NOT NULL,
    title VARCHAR(200) NOT NULL,
    status VARCHAR(20) DEFAULT 'OPEN' NOT NULL,
    details_json JSONB DEFAULT '{}'::jsonb NOT NULL,
    opened_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    resolved_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_hw_incidents_open ON hardware_integration_incidents (status, opened_at);

CREATE TABLE IF NOT EXISTS hardware_sync_audit_log (
    id VARCHAR(36) PRIMARY KEY,
    event_type VARCHAR(40) NOT NULL,
    entity_type VARCHAR(32) NOT NULL,
    entity_id VARCHAR(48),
    actor_id VARCHAR(64),
    summary VARCHAR(255) NOT NULL,
    payload_json JSONB DEFAULT '{}'::jsonb NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS hardware_player_certifications (
    id VARCHAR(36) PRIMARY KEY,
    player_id VARCHAR(36) NOT NULL,
    player_code VARCHAR(48) NOT NULL,
    certification_type VARCHAR(40) NOT NULL,
    status VARCHAR(20) DEFAULT 'VALID' NOT NULL,
    issuer VARCHAR(120),
    issued_at DATE,
    expires_at DATE,
    evidence_url VARCHAR(500),
    scope_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    CONSTRAINT uq_hw_player_cert UNIQUE (player_id, certification_type)
);

CREATE TABLE IF NOT EXISTS hardware_locker_corridors (
    id VARCHAR(36) PRIMARY KEY,
    corridor_code VARCHAR(64) NOT NULL UNIQUE,
    name VARCHAR(160) NOT NULL,
    origin_country VARCHAR(2) NOT NULL,
    dest_country VARCHAR(2) NOT NULL,
    handoff_type VARCHAR(32) DEFAULT 'LOCKER_TO_PUDO' NOT NULL,
    primary_player_id VARCHAR(36) NOT NULL,
    primary_player_code VARCHAR(48) NOT NULL,
    fallback_player_id VARCHAR(36),
    fallback_player_code VARCHAR(48),
    transit_hours_min INTEGER DEFAULT 4 NOT NULL,
    transit_hours_max INTEGER DEFAULT 48 NOT NULL,
    supports_returns BOOLEAN DEFAULT false NOT NULL,
    active BOOLEAN DEFAULT true NOT NULL,
    priority INTEGER DEFAULT 100 NOT NULL,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS hardware_corridor_handoff_steps (
    id VARCHAR(36) PRIMARY KEY,
    corridor_id VARCHAR(36) NOT NULL,
    step_order INTEGER NOT NULL,
    player_id VARCHAR(36) NOT NULL,
    player_code VARCHAR(48) NOT NULL,
    step_role VARCHAR(32) DEFAULT 'HANDOFF' NOT NULL,
    locker_id VARCHAR(120),
    notes TEXT,
    CONSTRAINT uq_hw_corridor_step UNIQUE (corridor_id, step_order)
);

CREATE TABLE IF NOT EXISTS hardware_corridor_sla (
    id VARCHAR(36) PRIMARY KEY,
    corridor_id VARCHAR(36) NOT NULL UNIQUE,
    corridor_code VARCHAR(64) NOT NULL,
    uptime_target_pct NUMERIC(5, 2) DEFAULT 99.50 NOT NULL,
    door_open_p95_ms INTEGER DEFAULT 2500 NOT NULL,
    sync_lag_max_sec INTEGER DEFAULT 300 NOT NULL,
    webhook_p95_latency_ms INTEGER DEFAULT 2000 NOT NULL,
    compliance_status VARCHAR(20) DEFAULT 'COMPLIANT' NOT NULL,
    breach_count INTEGER DEFAULT 0 NOT NULL,
    last_breach_at TIMESTAMPTZ,
    measured_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS hardware_onboarding_playbooks (
    code VARCHAR(32) PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    segment_code VARCHAR(32) NOT NULL,
    version VARCHAR(16) DEFAULT '1.0' NOT NULL,
    steps_json JSONB DEFAULT '[]'::jsonb NOT NULL,
    required_capabilities_json JSONB DEFAULT '[]'::jsonb NOT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL
);

CREATE TABLE IF NOT EXISTS hardware_onboarding_runs (
    id VARCHAR(36) PRIMARY KEY,
    subject_type VARCHAR(16) NOT NULL,
    subject_id VARCHAR(120) NOT NULL,
    playbook_code VARCHAR(32) NOT NULL,
    status VARCHAR(20) DEFAULT 'IN_PROGRESS' NOT NULL,
    current_step_order INTEGER DEFAULT 1 NOT NULL,
    blockers_json JSONB DEFAULT '[]'::jsonb NOT NULL,
    started_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    completed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS hardware_onboarding_milestones (
    id VARCHAR(36) PRIMARY KEY,
    run_id VARCHAR(36) NOT NULL,
    step_code VARCHAR(40) NOT NULL,
    step_order INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'PENDING' NOT NULL,
    evidence_json JSONB DEFAULT '{}'::jsonb NOT NULL,
    completed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS hardware_capability_webhooks (
    id VARCHAR(36) PRIMARY KEY,
    player_id VARCHAR(36) NOT NULL,
    player_code VARCHAR(48) NOT NULL,
    capability_code VARCHAR(40) NOT NULL,
    url VARCHAR(500) NOT NULL,
    secret_hash VARCHAR(128) NOT NULL,
    event_types_json JSONB DEFAULT '[]'::jsonb NOT NULL,
    active BOOLEAN DEFAULT true NOT NULL,
    last_http_status INTEGER,
    last_delivered_at TIMESTAMPTZ,
    last_error TEXT,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    CONSTRAINT uq_hw_cap_webhook UNIQUE (player_id, capability_code)
);

CREATE TABLE IF NOT EXISTS hardware_capability_webhook_deliveries (
    id VARCHAR(36) PRIMARY KEY,
    webhook_id VARCHAR(36) NOT NULL,
    event_type VARCHAR(40) NOT NULL,
    payload_json JSONB DEFAULT '{}'::jsonb NOT NULL,
    http_status INTEGER,
    success BOOLEAN DEFAULT false NOT NULL,
    response_snippet VARCHAR(500),
    status VARCHAR(20) DEFAULT 'FAILED' NOT NULL,
    attempt_count INTEGER DEFAULT 1 NOT NULL,
    dead_lettered_at TIMESTAMPTZ,
    replay_of_delivery_id VARCHAR(36),
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_hw_webhook_deliveries ON hardware_capability_webhook_deliveries (webhook_id, created_at);
