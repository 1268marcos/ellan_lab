-- Domínio partner estendido (settlements, service areas, billing, stores, SLA)

CREATE TABLE IF NOT EXISTS partner_settlement_batches (
    id character varying(36) NOT NULL PRIMARY KEY,
    partner_id character varying(36) NOT NULL,
    partner_type character varying(20) NOT NULL DEFAULT 'ECOMMERCE',
    period_start date NOT NULL,
    period_end date NOT NULL,
    currency character varying(8) NOT NULL DEFAULT 'BRL',
    total_orders integer NOT NULL DEFAULT 0,
    gross_revenue_cents bigint NOT NULL DEFAULT 0,
    revenue_share_pct numeric(6,4) NOT NULL,
    revenue_share_cents bigint NOT NULL DEFAULT 0,
    fees_cents bigint NOT NULL DEFAULT 0,
    net_amount_cents bigint NOT NULL DEFAULT 0,
    status character varying(20) NOT NULL DEFAULT 'DRAFT',
    settled_at timestamp with time zone,
    settlement_ref character varying(128),
    notes text,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS partner_settlement_items (
    id integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    batch_id character varying(36) NOT NULL,
    order_id character varying(36) NOT NULL,
    order_date timestamp with time zone NOT NULL,
    gross_cents bigint NOT NULL,
    share_pct numeric(6,4) NOT NULL,
    share_cents bigint NOT NULL,
    currency character varying(8) NOT NULL DEFAULT 'BRL'
);

CREATE TABLE IF NOT EXISTS partner_service_areas (
    id character varying(36) NOT NULL PRIMARY KEY,
    partner_id character varying(36) NOT NULL,
    partner_type character varying(20) NOT NULL DEFAULT 'ECOMMERCE',
    locker_id character varying(36) NOT NULL,
    priority integer NOT NULL DEFAULT 100,
    exclusive boolean NOT NULL DEFAULT false,
    valid_from date NOT NULL,
    valid_until date,
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamp with time zone NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS partner_performance_metrics (
    id character varying(36) NOT NULL PRIMARY KEY,
    partner_id character varying(36) NOT NULL,
    period_month character(7) NOT NULL,
    total_orders integer NOT NULL DEFAULT 0,
    on_time_pickup_pct numeric(5,2),
    return_rate_pct numeric(5,2),
    avg_pickup_hours numeric(6,2),
    sla_compliance_pct numeric(5,2),
    webhook_success_rate numeric(5,2),
    generated_at timestamp with time zone NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS partner_billing_plans (
    id character varying(36) NOT NULL PRIMARY KEY,
    partner_id character varying(36) NOT NULL,
    partner_type character varying(20) NOT NULL,
    plan_name character varying(128) NOT NULL,
    billing_model character varying(30) NOT NULL,
    currency character varying(8) NOT NULL DEFAULT 'BRL',
    monthly_fee_cents bigint,
    fee_per_delivery_cents bigint,
    valid_from date NOT NULL,
    valid_until date,
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS partner_billing_cycles (
    id character varying(36) NOT NULL PRIMARY KEY,
    partner_id character varying(36) NOT NULL,
    partner_type character varying(20) NOT NULL,
    billing_plan_id character varying(36) NOT NULL,
    period_start date NOT NULL,
    period_end date NOT NULL,
    total_amount_cents bigint NOT NULL DEFAULT 0,
    status character varying(20) NOT NULL DEFAULT 'OPEN',
    currency character varying(8) NOT NULL DEFAULT 'BRL',
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS partner_stores (
    id character varying(36) NOT NULL PRIMARY KEY,
    name character varying(128) NOT NULL,
    legal_name character varying(140),
    tax_id character varying(32),
    address_line character varying(255) NOT NULL,
    city character varying(100) NOT NULL,
    state character varying(50) NOT NULL,
    postal_code character varying(20) NOT NULL,
    phone character varying(32),
    email character varying(128),
    commission_pct numeric(5,2) DEFAULT 5.00,
    active boolean DEFAULT true,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS partner_sla_agreements (
    id character varying(36) NOT NULL PRIMARY KEY,
    partner_id character varying(36) NOT NULL,
    partner_type character varying(20) NOT NULL,
    country character varying(2) NOT NULL DEFAULT 'BR',
    sla_pickup_hours integer NOT NULL DEFAULT 72,
    sla_return_hours integer NOT NULL DEFAULT 24,
    penalty_pct numeric(5,2) DEFAULT 0,
    valid_from date NOT NULL,
    valid_until date,
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamp with time zone NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS partner_status_history (
    id character varying(36) NOT NULL PRIMARY KEY,
    partner_id character varying(36) NOT NULL,
    partner_type character varying(20) NOT NULL,
    from_status character varying(30),
    to_status character varying(30) NOT NULL,
    reason text,
    changed_by character varying(36),
    changed_at timestamp with time zone NOT NULL DEFAULT now()
);
