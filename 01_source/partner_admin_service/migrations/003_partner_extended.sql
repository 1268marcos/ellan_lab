-- Domínio partner estendido (observabilidade, billing B2B, onboarding)

CREATE TABLE IF NOT EXISTS partner_webhook_deliveries (
    id character varying(36) NOT NULL PRIMARY KEY,
    endpoint_id character varying(36) NOT NULL,
    event_id character varying(36) NOT NULL,
    event_type character varying(80) NOT NULL,
    payload_json text NOT NULL DEFAULT '{}',
    payload_hash character varying(64),
    http_status integer,
    attempt_count integer NOT NULL DEFAULT 0,
    status character varying(20) NOT NULL DEFAULT 'PENDING',
    last_error text,
    next_retry_at timestamp with time zone,
    processing_started_at timestamp with time zone,
    delivered_at timestamp with time zone,
    created_at timestamp with time zone NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS partner_integration_health (
    id integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    partner_id character varying(36) NOT NULL,
    partner_type character varying(20) NOT NULL,
    endpoint_url character varying(500),
    checked_at timestamp with time zone NOT NULL DEFAULT now(),
    status character varying(20) NOT NULL,
    latency_ms integer,
    http_status integer,
    error_message character varying(500)
);

CREATE TABLE IF NOT EXISTS partner_order_events_outbox (
    id character varying(36) NOT NULL PRIMARY KEY,
    partner_id character varying(36) NOT NULL,
    order_id character varying(36) NOT NULL,
    event_type character varying(50) NOT NULL,
    payload_json text NOT NULL DEFAULT '{}',
    api_version character varying(10) NOT NULL DEFAULT 'v1',
    status character varying(20) NOT NULL DEFAULT 'PENDING',
    attempt_count integer NOT NULL DEFAULT 0,
    max_attempts integer NOT NULL DEFAULT 5,
    next_retry_at timestamp with time zone,
    last_error text,
    delivered_at timestamp with time zone,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS partner_b2b_invoices (
    id character varying(36) NOT NULL PRIMARY KEY,
    cycle_id character varying(36) NOT NULL,
    partner_id character varying(36) NOT NULL,
    invoice_number character varying(50),
    document_type character varying(30) NOT NULL DEFAULT 'INVOICE',
    amount_cents bigint NOT NULL,
    tax_cents bigint NOT NULL DEFAULT 0,
    currency character varying(8) NOT NULL DEFAULT 'BRL',
    country_code character varying(2),
    due_date date,
    taker_name character varying(140),
    taker_email character varying(128),
    status character varying(20) NOT NULL DEFAULT 'DRAFT',
    issued_at timestamp with time zone,
    paid_at timestamp with time zone,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS partner_billing_line_items (
    id integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    cycle_id character varying(36) NOT NULL,
    partner_id character varying(36) NOT NULL,
    locker_id character varying(36),
    line_type character varying(40) NOT NULL,
    description character varying(255) NOT NULL,
    quantity numeric(12,4) NOT NULL DEFAULT 1,
    unit_price_cents bigint NOT NULL,
    total_cents bigint NOT NULL,
    currency character varying(8) NOT NULL DEFAULT 'BRL',
    created_at timestamp with time zone NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS partner_credit_notes (
    id character varying(36) NOT NULL PRIMARY KEY,
    partner_id character varying(36) NOT NULL,
    original_invoice_id character varying(36),
    cycle_id character varying(36),
    reason_code character varying(40) NOT NULL,
    description text NOT NULL,
    amount_cents bigint NOT NULL,
    currency character varying(8) NOT NULL DEFAULT 'BRL',
    status character varying(20) NOT NULL DEFAULT 'PENDING',
    approved_at timestamp with time zone,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS partner_payment_holds (
    id character varying(36) NOT NULL PRIMARY KEY,
    partner_id character varying(36) NOT NULL,
    invoice_id character varying(36) NOT NULL,
    hold_amount_cents bigint NOT NULL,
    release_schedule character varying(30) NOT NULL DEFAULT 'AFTER_15_DAYS',
    released_at timestamp with time zone,
    status character varying(20) NOT NULL DEFAULT 'HELD',
    created_at timestamp with time zone NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS partner_commission_structure (
    id character varying(36) NOT NULL PRIMARY KEY,
    partner_id character varying(36) NOT NULL,
    commission_percentage numeric(5,2),
    revenue_threshold_cents bigint,
    effective_from date
);

CREATE TABLE IF NOT EXISTS partner_onboarding_milestones (
    id character varying(36) NOT NULL PRIMARY KEY,
    partner_id character varying(36) NOT NULL,
    partner_type character varying(20) NOT NULL,
    milestone_code character varying(40) NOT NULL,
    milestone_label character varying(128) NOT NULL,
    status character varying(20) NOT NULL DEFAULT 'PENDING',
    sort_order integer NOT NULL DEFAULT 100,
    completed_at timestamp with time zone,
    completed_by character varying(36),
    notes text,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now()
);
