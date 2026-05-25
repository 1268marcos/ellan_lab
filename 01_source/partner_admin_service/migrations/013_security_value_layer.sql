-- Camada de valor OPS: risco, revisão de acesso, break-glass, alertas, templates, compliance

CREATE TABLE IF NOT EXISTS security_role_templates (
    id character varying(36) NOT NULL PRIMARY KEY,
    code character varying(48) NOT NULL UNIQUE,
    name character varying(128) NOT NULL,
    description character varying(500),
    roles_json text DEFAULT '[]' NOT NULL,
    permission_groups_json text DEFAULT '[]' NOT NULL,
    default_players_json text DEFAULT '[]' NOT NULL,
    target_segment character varying(32),
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS security_risk_scores (
    id character varying(36) NOT NULL PRIMARY KEY,
    entity_type character varying(32) NOT NULL,
    entity_id character varying(120) NOT NULL,
    score numeric(5,2) NOT NULL,
    risk_tier character varying(16) NOT NULL,
    factors_json text DEFAULT '[]' NOT NULL,
    computed_at timestamp with time zone DEFAULT now() NOT NULL,
    expires_at timestamp with time zone,
    UNIQUE (entity_type, entity_id)
);

CREATE TABLE IF NOT EXISTS security_access_review_campaigns (
    id character varying(36) NOT NULL PRIMARY KEY,
    name character varying(128) NOT NULL,
    status character varying(20) DEFAULT 'DRAFT' NOT NULL,
    due_at timestamp with time zone NOT NULL,
    scope_json text DEFAULT '{}' NOT NULL,
    created_by character varying(36),
    completed_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS security_access_review_items (
    id character varying(36) NOT NULL PRIMARY KEY,
    campaign_id character varying(36) NOT NULL REFERENCES security_access_review_campaigns(id) ON DELETE CASCADE,
    user_id character varying(36) NOT NULL,
    subject_type character varying(32) NOT NULL,
    subject_id character varying(120) NOT NULL,
    subject_label character varying(255),
    decision character varying(20),
    reviewer_id character varying(36),
    reviewed_at timestamp with time zone,
    notes text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS security_break_glass_events (
    id character varying(36) NOT NULL PRIMARY KEY,
    user_id character varying(36) NOT NULL,
    reason character varying(500) NOT NULL,
    granted_roles_json text DEFAULT '[]' NOT NULL,
    approved_by character varying(36),
    status character varying(20) DEFAULT 'ACTIVE' NOT NULL,
    started_at timestamp with time zone DEFAULT now() NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    revoked_at timestamp with time zone,
    audit_ref character varying(36)
);

CREATE TABLE IF NOT EXISTS security_alert_rules (
    id character varying(36) NOT NULL PRIMARY KEY,
    code character varying(48) NOT NULL UNIQUE,
    name character varying(128) NOT NULL,
    condition_type character varying(40) NOT NULL,
    threshold_json text DEFAULT '{}' NOT NULL,
    severity character varying(16) DEFAULT 'MEDIUM' NOT NULL,
    notify_channels_json text DEFAULT '["OPS_CONSOLE"]' NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS security_alerts (
    id character varying(36) NOT NULL PRIMARY KEY,
    rule_id character varying(36) NOT NULL REFERENCES security_alert_rules(id),
    title character varying(255) NOT NULL,
    detail text,
    entity_type character varying(32),
    entity_id character varying(120),
    severity character varying(16) NOT NULL,
    status character varying(20) DEFAULT 'OPEN' NOT NULL,
    acknowledged_by character varying(36),
    acknowledged_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS security_compliance_controls (
    code character varying(48) NOT NULL PRIMARY KEY,
    framework character varying(32) NOT NULL,
    title character varying(255) NOT NULL,
    description text,
    domain character varying(32),
    is_active boolean DEFAULT true NOT NULL
);

CREATE TABLE IF NOT EXISTS security_control_mappings (
    id character varying(36) NOT NULL PRIMARY KEY,
    control_code character varying(48) NOT NULL REFERENCES security_compliance_controls(code) ON DELETE CASCADE,
    object_key character varying(254) NOT NULL,
    coverage_level character varying(16) DEFAULT 'PARTIAL' NOT NULL,
    UNIQUE (control_code, object_key)
);

CREATE INDEX IF NOT EXISTS ix_sec_review_campaign_status ON security_access_review_campaigns (status, due_at);
CREATE INDEX IF NOT EXISTS ix_sec_alerts_status ON security_alerts (status, severity, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_sec_risk_tier ON security_risk_scores (risk_tier, score DESC);
