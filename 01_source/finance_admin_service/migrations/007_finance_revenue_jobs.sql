-- Revenue recognition (diferimento) + histórico de jobs agendados

CREATE TABLE IF NOT EXISTS partner_revenue_schedules (
    id character varying(36) NOT NULL PRIMARY KEY,
    partner_id character varying(36) NOT NULL,
    source_type character varying(40) NOT NULL,
    source_id character varying(60) NOT NULL,
    total_cents bigint NOT NULL,
    recognized_cents bigint DEFAULT 0 NOT NULL,
    deferred_cents bigint NOT NULL,
    recognition_method character varying(30) DEFAULT 'STRAIGHT_LINE' NOT NULL,
    period_start date NOT NULL,
    period_end date NOT NULL,
    currency character varying(8) DEFAULT 'BRL' NOT NULL,
    status character varying(20) DEFAULT 'ACTIVE' NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS partner_revenue_recognition_entries (
    id character varying(36) NOT NULL PRIMARY KEY,
    schedule_id character varying(36) NOT NULL,
    partner_id character varying(36) NOT NULL,
    recognition_date date NOT NULL,
    amount_cents bigint NOT NULL,
    entry_status character varying(20) DEFAULT 'RECOGNIZED' NOT NULL,
    fiscal_synced boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    UNIQUE (schedule_id, recognition_date)
);

CREATE TABLE IF NOT EXISTS finance_scheduled_job_runs (
    id character varying(36) NOT NULL PRIMARY KEY,
    job_code character varying(40) NOT NULL,
    started_at timestamp with time zone NOT NULL,
    finished_at timestamp with time zone,
    status character varying(20) DEFAULT 'RUNNING' NOT NULL,
    result_json text DEFAULT '{}' NOT NULL,
    error_message text
);

CREATE INDEX IF NOT EXISTS ix_finance_job_runs_code_started
    ON finance_scheduled_job_runs (job_code, started_at DESC);

ALTER TABLE partner_b2b_invoices ADD COLUMN fiscal_status character varying(20) DEFAULT 'PENDING';
ALTER TABLE partner_b2b_invoices ADD COLUMN fiscal_access_key character varying(80);
ALTER TABLE partner_b2b_invoices ADD COLUMN fiscal_pdf_url character varying(500);
