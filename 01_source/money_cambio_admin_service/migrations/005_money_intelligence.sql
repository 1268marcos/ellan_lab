-- Money Intelligence — readiness, insights, alertas FX, calendário settlement

CREATE TABLE IF NOT EXISTS money_player_readiness (
    player_code VARCHAR(48) PRIMARY KEY,
    readiness_score INTEGER DEFAULT 0 NOT NULL,
    grade CHAR(1) DEFAULT 'F' NOT NULL,
    fx_linked BOOLEAN DEFAULT false NOT NULL,
    fiscal_linked BOOLEAN DEFAULT false NOT NULL,
    compliance_ok BOOLEAN DEFAULT false NOT NULL,
    relation_count INTEGER DEFAULT 0 NOT NULL,
    corridor_count INTEGER DEFAULT 0 NOT NULL,
    detail_json JSONB DEFAULT '{}'::jsonb NOT NULL,
    computed_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS money_ecosystem_insight (
    id VARCHAR(36) PRIMARY KEY,
    player_code VARCHAR(48),
    corridor_code VARCHAR(48),
    insight_type VARCHAR(40) NOT NULL,
    severity VARCHAR(12) NOT NULL,
    title VARCHAR(200) NOT NULL,
    detail_json JSONB DEFAULT '{}'::jsonb NOT NULL,
    suggested_action TEXT,
    status VARCHAR(16) DEFAULT 'OPEN' NOT NULL,
    detected_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    resolved_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_mei_player_status ON money_ecosystem_insight (player_code, status);
CREATE INDEX IF NOT EXISTS ix_mei_severity ON money_ecosystem_insight (severity, status);

CREATE TABLE IF NOT EXISTS money_fx_alert_rule (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    base_currency CHAR(8) NOT NULL,
    quote_currency CHAR(8) NOT NULL,
    threshold_bps INTEGER NOT NULL,
    direction VARCHAR(8) DEFAULT 'BOTH' NOT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS money_fx_alert_event (
    id VARCHAR(36) PRIMARY KEY,
    rule_id VARCHAR(36) NOT NULL REFERENCES money_fx_alert_rule(id),
    base_currency CHAR(8) NOT NULL,
    quote_currency CHAR(8) NOT NULL,
    previous_rate NUMERIC(18, 8),
    current_rate NUMERIC(18, 8) NOT NULL,
    change_bps INTEGER NOT NULL,
    status VARCHAR(16) DEFAULT 'OPEN' NOT NULL,
    triggered_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    acknowledged_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS money_settlement_schedule (
    id VARCHAR(36) PRIMARY KEY,
    scope_type VARCHAR(16) NOT NULL,
    scope_code VARCHAR(48) NOT NULL,
    country_code CHAR(2) NOT NULL,
    settlement_currency CHAR(3) NOT NULL,
    settlement_days INTEGER DEFAULT 2 NOT NULL,
    cut_off_time_utc VARCHAR(8) DEFAULT '17:00' NOT NULL,
    weekend_policy VARCHAR(24) DEFAULT 'SKIP_WEEKEND' NOT NULL,
    notes TEXT,
    is_active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    UNIQUE (scope_type, scope_code, country_code)
);

CREATE INDEX IF NOT EXISTS ix_mss_scope ON money_settlement_schedule (scope_type, scope_code);
