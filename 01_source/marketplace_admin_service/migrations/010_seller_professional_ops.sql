-- Seller professional ops: tiers, compliance, performance, agreements, risk (global marketplace)

CREATE TABLE IF NOT EXISTS seller_tier_definitions (
    code character varying(32) NOT NULL PRIMARY KEY,
    name character varying(128) NOT NULL,
    min_gmv_cents bigint DEFAULT 0 NOT NULL,
    max_commission_pct numeric(5,2) DEFAULT 30.00 NOT NULL,
    monthly_fee_cents bigint DEFAULT 0 NOT NULL,
    benefits_json text DEFAULT '[]'::text NOT NULL,
    sort_order integer DEFAULT 100 NOT NULL,
    active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS seller_tier_enrollments (
    id character varying(36) NOT NULL PRIMARY KEY,
    seller_id character varying(36) NOT NULL,
    tier_code character varying(32) NOT NULL,
    status character varying(20) DEFAULT 'ACTIVE' NOT NULL,
    effective_from date NOT NULL,
    effective_to date,
    notes text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT fk_ste_tier FOREIGN KEY (tier_code) REFERENCES seller_tier_definitions (code)
);

CREATE TABLE IF NOT EXISTS seller_compliance_profiles (
    id character varying(36) NOT NULL PRIMARY KEY,
    seller_id character varying(36) NOT NULL,
    country character varying(2) DEFAULT 'BR' NOT NULL,
    tax_regime character varying(32) DEFAULT 'SIMPLES' NOT NULL,
    tax_id character varying(32),
    vat_number character varying(32),
    ioss_number character varying(32),
    fiscal_status character varying(20) DEFAULT 'PENDING' NOT NULL,
    cross_border_enabled boolean DEFAULT false NOT NULL,
    notes text,
    verified_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT uq_seller_compliance_country UNIQUE (seller_id, country)
);

CREATE TABLE IF NOT EXISTS seller_performance_monthly (
    id character varying(36) NOT NULL PRIMARY KEY,
    seller_id character varying(36) NOT NULL,
    month date NOT NULL,
    gmv_cents bigint DEFAULT 0 NOT NULL,
    order_count integer DEFAULT 0 NOT NULL,
    avg_rating numeric(3,2),
    defect_rate_pct numeric(5,2) DEFAULT 0 NOT NULL,
    on_time_pickup_pct numeric(5,2) DEFAULT 100 NOT NULL,
    chargeback_count integer DEFAULT 0 NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT uq_seller_perf_month UNIQUE (seller_id, month)
);

CREATE TABLE IF NOT EXISTS seller_agreements (
    id character varying(36) NOT NULL PRIMARY KEY,
    seller_id character varying(36) NOT NULL,
    agreement_type character varying(32) NOT NULL,
    version character varying(16) NOT NULL,
    status character varying(20) DEFAULT 'DRAFT' NOT NULL,
    document_ref character varying(255),
    signed_at timestamp with time zone,
    expires_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS seller_risk_assessments (
    id character varying(36) NOT NULL PRIMARY KEY,
    seller_id character varying(36) NOT NULL,
    risk_score integer DEFAULT 50 NOT NULL,
    risk_band character varying(16) DEFAULT 'MEDIUM' NOT NULL,
    factors_json text DEFAULT '[]'::text NOT NULL,
    assessed_at timestamp with time zone DEFAULT now() NOT NULL,
    next_review_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_seller_risk_score CHECK (((risk_score >= 0) AND (risk_score <= 100)))
);

CREATE INDEX IF NOT EXISTS ix_seller_tier_enrollments_seller ON seller_tier_enrollments (seller_id, status);
CREATE INDEX IF NOT EXISTS ix_seller_compliance_seller ON seller_compliance_profiles (seller_id, fiscal_status);
CREATE INDEX IF NOT EXISTS ix_seller_performance_seller ON seller_performance_monthly (seller_id, month DESC);
CREATE INDEX IF NOT EXISTS ix_seller_agreements_seller ON seller_agreements (seller_id, status);
CREATE INDEX IF NOT EXISTS ix_seller_risk_seller ON seller_risk_assessments (seller_id, assessed_at DESC);
