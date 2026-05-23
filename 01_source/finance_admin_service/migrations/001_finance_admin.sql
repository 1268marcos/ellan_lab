-- DDL alinhado a complete_schema_20260523_c.sql (domínio FINANCE / partner billing / wallet)

CREATE TABLE IF NOT EXISTS finance_partner_accounts (
    id character varying(36) NOT NULL PRIMARY KEY,
    code character varying(48) NOT NULL UNIQUE,
    name character varying(160) NOT NULL,
    partner_type character varying(20) NOT NULL,
    country_code character varying(2),
    tax_id character varying(32),
    currency character varying(8) DEFAULT 'BRL' NOT NULL,
    active boolean DEFAULT true NOT NULL,
    metadata_json text DEFAULT '{}' NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS partner_billing_plans (
    id character varying(36) NOT NULL PRIMARY KEY,
    partner_id character varying(36) NOT NULL,
    partner_type character varying(20) NOT NULL,
    plan_name character varying(128) NOT NULL,
    billing_model character varying(30) NOT NULL,
    currency character varying(8) DEFAULT 'BRL' NOT NULL,
    country_code character varying(2),
    monthly_fee_cents bigint,
    fee_per_delivery_cents bigint,
    fee_per_pickup_cents bigint,
    fee_per_day_stored_cents bigint,
    revenue_share_pct numeric(6,4),
    valid_from date NOT NULL,
    valid_until date,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS partner_billing_cycles (
    id character varying(36) NOT NULL PRIMARY KEY,
    partner_id character varying(36) NOT NULL,
    locker_id character varying(36),
    partner_type character varying(20) NOT NULL,
    billing_plan_id character varying(36) NOT NULL,
    currency character varying(8) DEFAULT 'BRL' NOT NULL,
    period_start date NOT NULL,
    period_end date NOT NULL,
    total_amount_cents bigint DEFAULT 0 NOT NULL,
    status character varying(20) DEFAULT 'OPEN' NOT NULL,
    notes text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS partner_b2b_invoices (
    id character varying(36) NOT NULL PRIMARY KEY,
    cycle_id character varying(36) NOT NULL,
    partner_id character varying(36) NOT NULL,
    invoice_number character varying(50),
    document_type character varying(30) DEFAULT 'INVOICE' NOT NULL,
    amount_cents bigint NOT NULL,
    tax_cents bigint DEFAULT 0 NOT NULL,
    currency character varying(8) DEFAULT 'BRL' NOT NULL,
    status character varying(20) DEFAULT 'DRAFT' NOT NULL,
    due_date date,
    issued_at timestamp with time zone,
    paid_at timestamp with time zone,
    metadata_json text DEFAULT '{}' NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS partner_api_keys (
    id character varying(36) NOT NULL PRIMARY KEY,
    partner_id character varying(36) NOT NULL,
    partner_type character varying(20) NOT NULL,
    key_prefix character varying(16) NOT NULL,
    key_hash character varying(128) NOT NULL,
    label character varying(64),
    scopes_json text DEFAULT '[]' NOT NULL,
    expires_at timestamp with time zone,
    last_used_at timestamp with time zone,
    revoked_at timestamp with time zone,
    created_by character varying(36),
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS partner_webhook_endpoints (
    id character varying(36) NOT NULL PRIMARY KEY,
    partner_id character varying(36) NOT NULL,
    partner_type character varying(20) NOT NULL,
    url character varying(500) NOT NULL,
    secret_hash character varying(128) NOT NULL,
    secret_key character varying(256),
    events_json text DEFAULT '["*"]' NOT NULL,
    api_version character varying(10) DEFAULT 'v1' NOT NULL,
    retry_policy text DEFAULT '{}' NOT NULL,
    active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS wallet_provider_catalog (
    id bigint PRIMARY KEY AUTOINCREMENT,
    code character varying(80) NOT NULL UNIQUE,
    name character varying(120) NOT NULL,
    metadata_json text DEFAULT '{}' NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS wallet_transactions (
    id character varying(36) NOT NULL PRIMARY KEY,
    wallet_id character varying(36) NOT NULL,
    order_id character varying,
    type character varying(30) NOT NULL,
    amount_cents bigint NOT NULL,
    balance_after_cents bigint NOT NULL,
    status character varying(20) DEFAULT 'PENDING' NOT NULL,
    external_reference character varying(255),
    description text,
    metadata_json text DEFAULT '{}' NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS finance_ops_invoices (
    id character varying(50) NOT NULL PRIMARY KEY,
    order_id character varying(100) NOT NULL,
    country character varying(5) NOT NULL,
    invoice_type character varying(20) NOT NULL,
    status character varying(30) NOT NULL,
    amount_cents bigint,
    currency character varying(10),
    locker_id character varying(64),
    error_message character varying(500),
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);

CREATE TABLE IF NOT EXISTS billing_processed_events (
    id character varying(36) NOT NULL PRIMARY KEY,
    event_id character varying(128) NOT NULL UNIQUE,
    order_id character varying(100),
    event_type character varying(64) NOT NULL,
    processed_at timestamp with time zone DEFAULT now() NOT NULL,
    payload_json text DEFAULT '{}' NOT NULL
);
