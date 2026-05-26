-- Ops intelligence: health score, playbooks, quotas, sync jobs, cross-border, API health, promoções

CREATE TABLE IF NOT EXISTS seller_health_snapshots (
    id character varying(36) NOT NULL PRIMARY KEY,
    seller_id character varying(36) NOT NULL,
    snapshot_date date NOT NULL,
    health_score numeric(5,2) NOT NULL,
    health_band character varying(16) NOT NULL,
    coverage_pct numeric(5,2) DEFAULT 0,
    readiness_avg numeric(5,2) DEFAULT 0,
    open_incidents integer DEFAULT 0,
    kyc_status character varying(20),
    risk_level character varying(16),
    factors_json text DEFAULT '[]',
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT uq_seller_health_day UNIQUE (seller_id, snapshot_date)
);

CREATE INDEX IF NOT EXISTS ix_seller_health_seller ON seller_health_snapshots (seller_id, snapshot_date DESC);

CREATE TABLE IF NOT EXISTS marketplace_ops_playbooks (
    id character varying(36) NOT NULL PRIMARY KEY,
    code character varying(48) NOT NULL UNIQUE,
    name character varying(160) NOT NULL,
    trigger_type character varying(32) NOT NULL,
    severity character varying(16) DEFAULT 'MEDIUM',
    steps_json text NOT NULL,
    owner_team character varying(64),
    active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS seller_channel_quotas (
    id character varying(36) NOT NULL PRIMARY KEY,
    seller_id character varying(36) NOT NULL,
    channel_partner_id character varying(36) NOT NULL,
    max_active_skus integer DEFAULT 1000,
    max_orders_per_day integer DEFAULT 500,
    max_lockers_linked integer DEFAULT 50,
    current_skus integer DEFAULT 0,
    current_orders_today integer DEFAULT 0,
    quota_status character varying(20) DEFAULT 'OK',
    reset_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT uq_seller_channel_quota UNIQUE (seller_id, channel_partner_id)
);

CREATE TABLE IF NOT EXISTS seller_catalog_sync_jobs (
    id character varying(36) NOT NULL PRIMARY KEY,
    seller_id character varying(36) NOT NULL,
    channel_partner_id character varying(36) NOT NULL,
    job_type character varying(32) NOT NULL,
    status character varying(20) DEFAULT 'QUEUED' NOT NULL,
    items_total integer DEFAULT 0,
    items_ok integer DEFAULT 0,
    items_failed integer DEFAULT 0,
    started_at timestamp with time zone,
    finished_at timestamp with time zone,
    error_summary text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_sc_sync_seller ON seller_catalog_sync_jobs (seller_id, status, created_at DESC);

CREATE TABLE IF NOT EXISTS seller_cross_border_profiles (
    id character varying(36) NOT NULL PRIMARY KEY,
    seller_id character varying(36) NOT NULL,
    corridor_code character varying(48) NOT NULL,
    customs_scheme character varying(32) NOT NULL,
    ioss_number character varying(64),
    vat_number character varying(64),
    eori_number character varying(64),
    origin_country character varying(2) NOT NULL,
    dest_country character varying(2) NOT NULL,
    status character varying(20) DEFAULT 'PENDING',
    verified_at timestamp with time zone,
    notes text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT uq_seller_cross_border UNIQUE (seller_id, corridor_code)
);

CREATE TABLE IF NOT EXISTS marketplace_partner_api_health (
    id character varying(36) NOT NULL PRIMARY KEY,
    channel_partner_id character varying(36) NOT NULL,
    partner_code character varying(48) NOT NULL,
    measured_at timestamp with time zone NOT NULL,
    availability_pct numeric(5,2) DEFAULT 100,
    p95_latency_ms integer DEFAULT 0,
    error_rate_pct numeric(5,2) DEFAULT 0,
    rate_limit_hits integer DEFAULT 0,
    health_status character varying(16) DEFAULT 'HEALTHY',
    notes text
);

CREATE INDEX IF NOT EXISTS ix_mp_api_health_partner ON marketplace_partner_api_health (channel_partner_id, measured_at DESC);

CREATE TABLE IF NOT EXISTS seller_promotion_campaigns (
    id character varying(36) NOT NULL PRIMARY KEY,
    seller_id character varying(36) NOT NULL,
    channel_partner_id character varying(36) NOT NULL,
    campaign_code character varying(64) NOT NULL,
    name character varying(160) NOT NULL,
    discount_pct numeric(5,2),
    starts_at timestamp with time zone NOT NULL,
    ends_at timestamp with time zone NOT NULL,
    status character varying(20) DEFAULT 'DRAFT',
    budget_cents bigint DEFAULT 0,
    spent_cents bigint DEFAULT 0,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT uq_seller_promo_code UNIQUE (seller_id, campaign_code)
);

CREATE INDEX IF NOT EXISTS ix_seller_promo_status ON seller_promotion_campaigns (seller_id, status);
