-- DDL alinhado ao schema public (complete_schema_20260521_c.sql)
-- Tabelas gerenciadas pelo marketplace_admin_service

CREATE TABLE IF NOT EXISTS marketplace_sellers (
    id character varying(36) NOT NULL PRIMARY KEY,
    legal_name character varying(140) NOT NULL,
    trade_name character varying(140),
    tax_id character varying(32) NOT NULL UNIQUE,
    email character varying(128) NOT NULL,
    phone character varying(32),
    website character varying(255),
    status character varying(20) DEFAULT 'PENDING_APPROVAL' NOT NULL,
    commission_pct numeric(5,2) DEFAULT 5.00 NOT NULL,
    monthly_fee_cents bigint DEFAULT 0 NOT NULL,
    seller_rating numeric(3,2) DEFAULT 0,
    total_sales_cents bigint DEFAULT 0,
    total_orders integer DEFAULT 0,
    joined_at timestamp with time zone DEFAULT now(),
    approved_at timestamp with time zone,
    suspended_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    created_by character varying(36),
    updated_by character varying(36),
    deleted_at timestamp with time zone
);

CREATE TABLE IF NOT EXISTS seller_products (
    id character varying(36) NOT NULL PRIMARY KEY,
    seller_id character varying(36) NOT NULL,
    locker_id character varying(36) NOT NULL,
    product_id character varying(255) NOT NULL,
    seller_sku character varying(64),
    price_cents integer NOT NULL,
    quantity integer DEFAULT 0 NOT NULL,
    max_quantity_per_order integer DEFAULT 10,
    status character varying(20) DEFAULT 'ACTIVE' NOT NULL,
    priority integer DEFAULT 100,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    deleted_at timestamp with time zone,
    CONSTRAINT uq_seller_product_locker UNIQUE (seller_id, locker_id, product_id)
);

CREATE TABLE IF NOT EXISTS marketplace_commissions (
    id character varying(36) NOT NULL PRIMARY KEY,
    seller_id character varying(36) NOT NULL,
    order_id character varying(36) NOT NULL,
    order_item_id bigint,
    commission_rate_pct numeric(5,2) NOT NULL,
    commission_amount_cents integer NOT NULL,
    ellan_fee_cents integer NOT NULL,
    payment_gateway_fee_cents integer NOT NULL,
    net_to_seller_cents integer NOT NULL,
    status character varying(20) DEFAULT 'PENDING' NOT NULL,
    settled_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now()
);

CREATE TABLE IF NOT EXISTS seller_reviews (
    id character varying(36) NOT NULL PRIMARY KEY,
    seller_id character varying(36) NOT NULL,
    order_id character varying(36) NOT NULL,
    user_id character varying(36),
    rating integer NOT NULL,
    comment text,
    delivery_rating integer,
    product_quality_rating integer,
    communication_rating integer,
    verified_purchase boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT now()
);

CREATE TABLE IF NOT EXISTS seller_webhook_endpoints (
    id character varying(36) NOT NULL PRIMARY KEY,
    seller_id character varying(36) NOT NULL UNIQUE,
    url character varying(500) NOT NULL,
    secret_hash character varying(128) NOT NULL,
    secret_key character varying(256),
    events_json text DEFAULT '["*"]' NOT NULL,
    api_version character varying(10) DEFAULT 'v1' NOT NULL,
    active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS seller_api_keys (
    id character varying(36) NOT NULL PRIMARY KEY,
    seller_id character varying(36) NOT NULL,
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

CREATE INDEX IF NOT EXISTS ix_marketplace_sellers_status ON marketplace_sellers (status);
CREATE INDEX IF NOT EXISTS ix_seller_products_seller ON seller_products (seller_id, status);
CREATE INDEX IF NOT EXISTS ix_marketplace_commissions_order ON marketplace_commissions (order_id, status);
CREATE INDEX IF NOT EXISTS ix_seller_reviews_seller ON seller_reviews (seller_id, rating);
