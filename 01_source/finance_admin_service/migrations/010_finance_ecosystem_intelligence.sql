-- Inteligência de ecossistema: insights, benchmarks, health checks

CREATE TABLE IF NOT EXISTS finance_ecosystem_insights (
    id character varying(36) NOT NULL PRIMARY KEY,
    catalog_code character varying(48) NOT NULL,
    insight_type character varying(40) NOT NULL,
    severity character varying(10) DEFAULT 'MEDIUM' NOT NULL,
    title character varying(200) NOT NULL,
    detail_json text DEFAULT '{}' NOT NULL,
    suggested_action text,
    status character varying(20) DEFAULT 'OPEN' NOT NULL,
    detected_at timestamp with time zone DEFAULT now() NOT NULL,
    resolved_at timestamp with time zone,
    UNIQUE (catalog_code, insight_type, title)
);

CREATE INDEX IF NOT EXISTS ix_fei_catalog_status ON finance_ecosystem_insights (catalog_code, status, severity);

CREATE TABLE IF NOT EXISTS finance_player_benchmarks (
    catalog_code character varying(48) NOT NULL PRIMARY KEY,
    segment_code character varying(40) NOT NULL,
    readiness_score integer DEFAULT 0 NOT NULL,
    readiness_rank integer,
    readiness_percentile numeric(5,2),
    relation_count integer DEFAULT 0 NOT NULL,
    capability_count integer DEFAULT 0 NOT NULL,
    coverage_count integer DEFAULT 0 NOT NULL,
    estimated_locker_count integer,
    integration_status character varying(20),
    composite_score integer DEFAULT 0 NOT NULL,
    computed_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_fpb_segment_score ON finance_player_benchmarks (segment_code, composite_score DESC);

CREATE TABLE IF NOT EXISTS finance_integration_health_checks (
    id character varying(36) NOT NULL PRIMARY KEY,
    catalog_code character varying(48) NOT NULL,
    check_type character varying(40) NOT NULL,
    status character varying(20) DEFAULT 'UNKNOWN' NOT NULL,
    latency_ms integer,
    http_status integer,
    message text,
    checked_at timestamp with time zone DEFAULT now() NOT NULL,
    UNIQUE (catalog_code, check_type)
);

CREATE INDEX IF NOT EXISTS ix_fihc_status ON finance_integration_health_checks (status, checked_at DESC);
