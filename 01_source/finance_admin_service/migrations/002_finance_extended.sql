-- Extensão FINANCE — settlements, treasury, PnL locker, gaps fiscais, line items, webhook DLQ

CREATE TABLE IF NOT EXISTS partner_billing_line_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cycle_id character varying(36) NOT NULL,
    partner_id character varying(36) NOT NULL,
    locker_id character varying(36),
    line_type character varying(40) NOT NULL,
    description character varying(255) NOT NULL,
    quantity numeric(12,4) DEFAULT 1 NOT NULL,
    unit_price_cents bigint NOT NULL,
    total_cents bigint NOT NULL,
    currency character varying(8) DEFAULT 'BRL' NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS partner_settlement_batches (
    id character varying(36) NOT NULL PRIMARY KEY,
    partner_id character varying(36) NOT NULL,
    partner_type character varying(20) DEFAULT 'ECOMMERCE' NOT NULL,
    period_start date NOT NULL,
    period_end date NOT NULL,
    currency character varying(8) DEFAULT 'BRL' NOT NULL,
    total_orders integer DEFAULT 0 NOT NULL,
    gross_revenue_cents bigint DEFAULT 0 NOT NULL,
    revenue_share_pct numeric(6,4) NOT NULL,
    revenue_share_cents bigint DEFAULT 0 NOT NULL,
    fees_cents bigint DEFAULT 0 NOT NULL,
    net_amount_cents bigint DEFAULT 0 NOT NULL,
    status character varying(20) DEFAULT 'DRAFT' NOT NULL,
    settled_at timestamp with time zone,
    settlement_ref character varying(128),
    notes text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS partner_settlement_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id character varying(36) NOT NULL,
    order_id character varying(36) NOT NULL,
    order_date timestamp with time zone NOT NULL,
    gross_cents bigint NOT NULL,
    share_pct numeric(6,4) NOT NULL,
    share_cents bigint NOT NULL,
    currency character varying(8) DEFAULT 'BRL' NOT NULL
);

CREATE TABLE IF NOT EXISTS partner_credit_notes (
    id character varying(36) NOT NULL PRIMARY KEY,
    partner_id character varying(36) NOT NULL,
    original_invoice_id character varying(36),
    cycle_id character varying(36),
    reason_code character varying(40) NOT NULL,
    description text NOT NULL,
    amount_cents bigint NOT NULL,
    currency character varying(8) DEFAULT 'BRL' NOT NULL,
    status character varying(20) DEFAULT 'PENDING' NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS partner_payment_holds (
    id character varying(36) NOT NULL PRIMARY KEY,
    partner_id character varying(36) NOT NULL,
    invoice_id character varying(36) NOT NULL,
    hold_amount_cents bigint NOT NULL,
    release_schedule character varying(30) DEFAULT 'AFTER_15_DAYS' NOT NULL,
    released_at timestamp with time zone,
    status character varying(20) DEFAULT 'HELD' NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS partner_commission_structure (
    id character varying(36) NOT NULL PRIMARY KEY,
    partner_id character varying(36) NOT NULL,
    commission_percentage numeric(5,2) NOT NULL,
    revenue_threshold_cents bigint,
    effective_from date NOT NULL,
    effective_until date,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS cost_centers (
    id character varying(36) NOT NULL PRIMARY KEY,
    locker_id character varying(120) NOT NULL UNIQUE,
    region_code character varying(20),
    network_code character varying(48),
    operational_cost_monthly_cents bigint DEFAULT 0,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS cost_center_monthly (
    id character varying(36) NOT NULL PRIMARY KEY,
    locker_id character varying(120) NOT NULL,
    month date NOT NULL,
    rent_cents bigint DEFAULT 0,
    maintenance_preventive_cents bigint DEFAULT 0,
    maintenance_corrective_cents bigint DEFAULT 0,
    connectivity_cents bigint DEFAULT 0,
    energy_cents bigint DEFAULT 0,
    insurance_cents bigint DEFAULT 0,
    payment_gateway_fee_cents bigint DEFAULT 0,
    depreciation_cents bigint DEFAULT 0,
    cleaning_cents bigint DEFAULT 0,
    security_cents bigint DEFAULT 0,
    marketing_cents bigint DEFAULT 0,
    other_cents bigint DEFAULT 0,
    notes text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    UNIQUE (locker_id, month)
);

CREATE TABLE IF NOT EXISTS fiscal_reconciliation_gaps (
    id character varying(60) NOT NULL PRIMARY KEY,
    dedupe_key character varying(180) NOT NULL UNIQUE,
    gap_type character varying(80) NOT NULL,
    severity character varying(20) NOT NULL,
    status character varying(20) NOT NULL,
    order_id character varying(100),
    invoice_id character varying(50),
    details_json text DEFAULT '{}',
    first_detected_at timestamp with time zone NOT NULL,
    last_detected_at timestamp with time zone NOT NULL,
    resolved_at timestamp with time zone
);

CREATE TABLE IF NOT EXISTS partner_webhook_deliveries (
    id character varying(36) NOT NULL PRIMARY KEY,
    endpoint_id character varying(36) NOT NULL,
    event_id character varying(36) NOT NULL,
    event_type character varying(80) NOT NULL,
    payload_json text DEFAULT '{}' NOT NULL,
    http_status integer,
    attempt_count integer DEFAULT 0 NOT NULL,
    status character varying(20) DEFAULT 'PENDING' NOT NULL,
    last_error text,
    delivered_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);
