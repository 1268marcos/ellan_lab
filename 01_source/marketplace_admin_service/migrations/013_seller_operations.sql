-- Operações seller: onboarding, SKU canal, preços, devoluções, notificações, alocação inventário

CREATE TABLE IF NOT EXISTS seller_onboarding_tasks (
    id character varying(36) NOT NULL PRIMARY KEY,
    seller_id character varying(36) NOT NULL,
    task_code character varying(48) NOT NULL,
    title character varying(160) NOT NULL,
    category character varying(32) NOT NULL,
    status character varying(20) DEFAULT 'PENDING' NOT NULL,
    required boolean DEFAULT true NOT NULL,
    sort_order integer DEFAULT 100 NOT NULL,
    completed_at timestamp with time zone,
    completed_by character varying(64),
    notes text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT uq_seller_onboarding_task UNIQUE (seller_id, task_code)
);

CREATE INDEX IF NOT EXISTS ix_seller_onboarding_seller ON seller_onboarding_tasks (seller_id, status);

CREATE TABLE IF NOT EXISTS seller_channel_sku_maps (
    id character varying(36) NOT NULL PRIMARY KEY,
    seller_id character varying(36) NOT NULL,
    channel_partner_id character varying(36) NOT NULL,
    internal_sku character varying(64) NOT NULL,
    channel_sku character varying(128) NOT NULL,
    seller_product_id character varying(36),
    active boolean DEFAULT true NOT NULL,
    last_synced_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT uq_seller_channel_sku UNIQUE (seller_id, channel_partner_id, internal_sku)
);

CREATE INDEX IF NOT EXISTS ix_scsm_seller ON seller_channel_sku_maps (seller_id, channel_partner_id);

CREATE TABLE IF NOT EXISTS seller_pricing_rules (
    id character varying(36) NOT NULL PRIMARY KEY,
    seller_id character varying(36) NOT NULL,
    channel_partner_id character varying(36),
    rule_type character varying(32) NOT NULL,
    name character varying(128) NOT NULL,
    min_price_cents integer,
    max_discount_pct numeric(5,2),
    markup_pct numeric(5,2),
    currency character varying(8) DEFAULT 'BRL',
    priority integer DEFAULT 100 NOT NULL,
    active boolean DEFAULT true NOT NULL,
    valid_from timestamp with time zone,
    valid_until timestamp with time zone,
    conditions_json text DEFAULT '{}',
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_spr_seller ON seller_pricing_rules (seller_id, active);

CREATE TABLE IF NOT EXISTS seller_return_policies (
    id character varying(36) NOT NULL PRIMARY KEY,
    seller_id character varying(36) NOT NULL,
    channel_partner_id character varying(36),
    policy_code character varying(48) NOT NULL,
    return_window_days integer DEFAULT 7 NOT NULL,
    restocking_fee_pct numeric(5,2) DEFAULT 0,
    accepts_locker_return boolean DEFAULT true NOT NULL,
    rma_required boolean DEFAULT true NOT NULL,
    status character varying(20) DEFAULT 'ACTIVE',
    notes text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT uq_seller_return_policy UNIQUE (seller_id, policy_code)
);

CREATE TABLE IF NOT EXISTS seller_notification_subscriptions (
    id character varying(36) NOT NULL PRIMARY KEY,
    seller_id character varying(36) NOT NULL,
    event_type character varying(48) NOT NULL,
    channel character varying(24) NOT NULL,
    destination character varying(255) NOT NULL,
    active boolean DEFAULT true NOT NULL,
    locale character varying(8) DEFAULT 'pt-BR',
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT uq_seller_notif_sub UNIQUE (seller_id, event_type, channel, destination)
);

CREATE TABLE IF NOT EXISTS seller_inventory_allocations (
    id character varying(36) NOT NULL PRIMARY KEY,
    seller_id character varying(36) NOT NULL,
    seller_product_id character varying(36) NOT NULL,
    channel_partner_id character varying(36) NOT NULL,
    locker_id character varying(36),
    allocated_qty integer DEFAULT 0 NOT NULL,
    reserved_qty integer DEFAULT 0 NOT NULL,
    available_qty integer DEFAULT 0 NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT uq_seller_inv_alloc UNIQUE (seller_id, seller_product_id, channel_partner_id, locker_id)
);

CREATE INDEX IF NOT EXISTS ix_sia_seller ON seller_inventory_allocations (seller_id, channel_partner_id);

CREATE TABLE IF NOT EXISTS seller_fulfillment_preferences (
    id character varying(36) NOT NULL PRIMARY KEY,
    seller_id character varying(36) NOT NULL,
    default_locker_id character varying(36),
    split_shipments_allowed boolean DEFAULT false NOT NULL,
    max_packages_per_order integer DEFAULT 1,
    prefer_nearest_locker boolean DEFAULT true NOT NULL,
    handoff_mode character varying(24) DEFAULT 'LOCKER_FIRST',
    packaging_notes text,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT uq_seller_fulfillment_pref UNIQUE (seller_id)
);
