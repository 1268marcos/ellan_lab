-- Catálogo mundial de players locker/marketplace para FINANCE

CREATE TABLE IF NOT EXISTS finance_locker_network_catalog (
    id character varying(36) NOT NULL PRIMARY KEY,
    code character varying(48) NOT NULL UNIQUE,
    name character varying(160) NOT NULL,
    player_role character varying(40) NOT NULL,
    parent_group character varying(40) NOT NULL,
    country_code character varying(2) NOT NULL,
    regions_json text DEFAULT '[]' NOT NULL,
    supports_lockers boolean DEFAULT true NOT NULL,
    supports_marketplace boolean DEFAULT false NOT NULL,
    global_tier character varying(20) DEFAULT 'REGIONAL' NOT NULL,
    locker_operator_ref character varying(48),
    default_billing_model character varying(30) DEFAULT 'HYBRID' NOT NULL,
    default_revenue_share_pct numeric(6,4),
    monthly_fee_cents bigint,
    integration_status character varying(20) DEFAULT 'PLANNED' NOT NULL,
    estimated_locker_count integer,
    finance_partner_id character varying(36),
    api_docs_url character varying(500),
    notes text,
    sort_order integer DEFAULT 100 NOT NULL,
    active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_flnc_parent_country ON finance_locker_network_catalog (parent_group, country_code, active);
CREATE INDEX IF NOT EXISTS ix_flnc_finance_partner ON finance_locker_network_catalog (finance_partner_id);
