-- Fiscal Intelligence: insights operacionais e eventos de contingência SEFAZ/AT

CREATE TABLE IF NOT EXISTS fiscal_ops_insights (
    id character varying(36) NOT NULL PRIMARY KEY,
    entity_type character varying(32) NOT NULL,
    entity_ref character varying(64) NOT NULL,
    insight_type character varying(40) NOT NULL,
    severity character varying(10) DEFAULT 'MEDIUM' NOT NULL,
    title character varying(200) NOT NULL,
    detail_json text DEFAULT '{}' NOT NULL,
    suggested_action text,
    status character varying(20) DEFAULT 'OPEN' NOT NULL,
    detected_at timestamp with time zone DEFAULT now() NOT NULL,
    resolved_at timestamp with time zone
);

CREATE INDEX IF NOT EXISTS ix_foi_entity_status ON fiscal_ops_insights (entity_type, entity_ref, status, severity);

CREATE TABLE IF NOT EXISTS fiscal_contingency_events (
    id character varying(36) NOT NULL PRIMARY KEY,
    country character varying(5) NOT NULL,
    region_code character varying(20),
    authority character varying(80) NOT NULL,
    contingency_mode character varying(32) NOT NULL,
    reason character varying(500),
    issuer_code character varying(32),
    active boolean DEFAULT true NOT NULL,
    started_at timestamp with time zone DEFAULT now() NOT NULL,
    ended_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_fce_active_country ON fiscal_contingency_events (active, country, started_at DESC);
