-- Domínio FINANCE avançado: termos, FX, tiers, dunning, reconciliação, fiscal, documentos, auditoria

CREATE TABLE IF NOT EXISTS partner_payment_terms (
    id character varying(36) NOT NULL PRIMARY KEY,
    partner_id character varying(36) NOT NULL,
    net_days integer DEFAULT 30 NOT NULL,
    grace_days integer DEFAULT 0 NOT NULL,
    early_payment_discount_pct numeric(6, 4),
    currency character varying(8) DEFAULT 'BRL' NOT NULL,
    is_default boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS finance_fx_rates (
    id character varying(36) NOT NULL PRIMARY KEY,
    base_currency character varying(8) NOT NULL,
    quote_currency character varying(8) NOT NULL,
    rate_date date NOT NULL,
    rate numeric(18, 8) NOT NULL,
    source character varying(40) DEFAULT 'MANUAL' NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    UNIQUE (base_currency, quote_currency, rate_date)
);

CREATE TABLE IF NOT EXISTS partner_commercial_tiers (
    tier_code character varying(24) NOT NULL PRIMARY KEY,
    name character varying(80) NOT NULL,
    min_monthly_orders integer DEFAULT 0 NOT NULL,
    min_gmv_cents bigint DEFAULT 0 NOT NULL,
    default_revenue_share_pct numeric(6, 4),
    sort_order integer DEFAULT 100 NOT NULL
);

CREATE TABLE IF NOT EXISTS partner_tier_assignments (
    id character varying(36) NOT NULL PRIMARY KEY,
    partner_id character varying(36) NOT NULL,
    tier_code character varying(24) NOT NULL,
    effective_from date NOT NULL,
    effective_until date,
    assigned_by character varying(80) DEFAULT 'system',
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS partner_dunning_policies (
    id character varying(36) NOT NULL PRIMARY KEY,
    partner_id character varying(36),
    stage integer NOT NULL,
    days_overdue integer NOT NULL,
    action character varying(40) NOT NULL,
    notify_channel character varying(20) DEFAULT 'EMAIL',
    active boolean DEFAULT true NOT NULL
);

CREATE TABLE IF NOT EXISTS partner_dunning_cases (
    id character varying(36) NOT NULL PRIMARY KEY,
    invoice_id character varying(36) NOT NULL,
    partner_id character varying(36) NOT NULL,
    stage integer DEFAULT 1 NOT NULL,
    amount_due_cents bigint NOT NULL,
    status character varying(20) DEFAULT 'OPEN' NOT NULL,
    next_action_at timestamp with time zone,
    resolved_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS settlement_reconciliation_runs (
    id character varying(36) NOT NULL PRIMARY KEY,
    batch_id character varying(36) NOT NULL,
    run_at timestamp with time zone DEFAULT now() NOT NULL,
    status character varying(20) DEFAULT 'COMPLETED' NOT NULL,
    matched_count integer DEFAULT 0 NOT NULL,
    unmatched_count integer DEFAULT 0 NOT NULL,
    variance_cents bigint DEFAULT 0 NOT NULL
);

CREATE TABLE IF NOT EXISTS settlement_reconciliation_matches (
    id integer PRIMARY KEY AUTOINCREMENT,
    run_id character varying(36) NOT NULL,
    settlement_item_id integer,
    order_id character varying(36) NOT NULL,
    wallet_tx_id character varying(36),
    match_status character varying(20) NOT NULL,
    variance_cents bigint DEFAULT 0 NOT NULL
);

CREATE TABLE IF NOT EXISTS partner_tax_corridors (
    id character varying(36) NOT NULL PRIMARY KEY,
    partner_id character varying(36) NOT NULL,
    origin_country character varying(2) NOT NULL,
    destination_country character varying(2) NOT NULL,
    document_type character varying(30) DEFAULT 'NF_B2B' NOT NULL,
    tax_regime character varying(40) NOT NULL,
    withholding_pct numeric(6, 4) DEFAULT 0,
    active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS partner_invoice_documents (
    id character varying(36) NOT NULL PRIMARY KEY,
    invoice_id character varying(36) NOT NULL,
    document_kind character varying(20) NOT NULL,
    storage_uri character varying(500),
    access_key character varying(80),
    fiscal_invoice_id character varying(60),
    country character varying(2) NOT NULL,
    invoice_type character varying(30) DEFAULT 'B2B',
    issued_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS finance_audit_log (
    id character varying(36) NOT NULL PRIMARY KEY,
    actor_id character varying(80) DEFAULT 'system',
    action character varying(60) NOT NULL,
    entity_type character varying(40) NOT NULL,
    entity_id character varying(60) NOT NULL,
    before_json text DEFAULT '{}',
    after_json text DEFAULT '{}',
    created_at timestamp with time zone DEFAULT now() NOT NULL
);
