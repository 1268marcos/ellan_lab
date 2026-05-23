-- FINANCE OPS profissional: contratos, roadmap, readiness, SLAs

CREATE TABLE IF NOT EXISTS partner_commercial_contracts (
    id character varying(36) NOT NULL PRIMARY KEY,
    partner_id character varying(36) NOT NULL,
    catalog_code character varying(48),
    contract_type character varying(40) NOT NULL,
    title character varying(200) NOT NULL,
    effective_from date NOT NULL,
    effective_until date,
    currency character varying(8) DEFAULT 'BRL' NOT NULL,
    status character varying(20) DEFAULT 'ACTIVE' NOT NULL,
    billing_plan_id character varying(36),
    metadata_json text DEFAULT '{}' NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS finance_integration_milestones (
    id character varying(36) NOT NULL PRIMARY KEY,
    catalog_code character varying(48) NOT NULL,
    phase character varying(40) NOT NULL,
    title character varying(160) NOT NULL,
    target_date date,
    completed_at timestamp with time zone,
    status character varying(20) DEFAULT 'PENDING' NOT NULL,
    owner character varying(80),
    blocker_notes text,
    sort_order integer DEFAULT 100 NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS finance_partner_readiness (
    catalog_code character varying(48) NOT NULL PRIMARY KEY,
    readiness_score integer DEFAULT 0 NOT NULL,
    integration_score integer DEFAULT 0 NOT NULL,
    billing_score integer DEFAULT 0 NOT NULL,
    compliance_score integer DEFAULT 0 NOT NULL,
    grade character varying(4) DEFAULT 'D' NOT NULL,
    blockers_json text DEFAULT '[]' NOT NULL,
    computed_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS partner_sla_definitions (
    id character varying(36) NOT NULL PRIMARY KEY,
    partner_id character varying(36) NOT NULL,
    catalog_code character varying(48),
    metric_code character varying(60) NOT NULL,
    metric_name character varying(120) NOT NULL,
    target_value numeric(12, 4) NOT NULL,
    target_unit character varying(20) NOT NULL,
    window_days integer DEFAULT 30 NOT NULL,
    penalty_credit_pct numeric(6, 4),
    active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS partner_sla_breaches (
    id character varying(36) NOT NULL PRIMARY KEY,
    sla_id character varying(36) NOT NULL,
    partner_id character varying(36) NOT NULL,
    observed_value numeric(12, 4) NOT NULL,
    breach_at timestamp with time zone NOT NULL,
    status character varying(20) DEFAULT 'OPEN' NOT NULL,
    credit_note_id character varying(36),
    notes text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);
