-- Players do ecossistema locker + marketplace (InPost, DHL, Magalu, ML, Amazon, etc.)

CREATE TABLE IF NOT EXISTS marketplace_channel_partners (
    id character varying(36) NOT NULL PRIMARY KEY,
    code character varying(32) NOT NULL UNIQUE,
    name character varying(128) NOT NULL,
    partner_role character varying(32) NOT NULL,
    country character varying(2) NOT NULL DEFAULT 'BR',
    website character varying(255),
    integration_type character varying(30) DEFAULT 'REST',
    locker_operator_ref character varying(64),
    ecommerce_partner_code character varying(32),
    supports_marketplace boolean DEFAULT true NOT NULL,
    supports_lockers boolean DEFAULT false NOT NULL,
    active boolean DEFAULT true NOT NULL,
    sort_order integer DEFAULT 100 NOT NULL,
    notes text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS seller_channel_listings (
    id character varying(36) NOT NULL PRIMARY KEY,
    seller_id character varying(36) NOT NULL,
    channel_partner_id character varying(36) NOT NULL,
    external_store_id character varying(128),
    listing_status character varying(20) DEFAULT 'ACTIVE' NOT NULL,
    commission_override_pct numeric(5,2),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT uq_seller_channel_listing UNIQUE (seller_id, channel_partner_id)
);

CREATE TABLE IF NOT EXISTS seller_locker_network_links (
    id character varying(36) NOT NULL PRIMARY KEY,
    seller_id character varying(36) NOT NULL,
    channel_partner_id character varying(36) NOT NULL,
    locker_id character varying(36),
    priority integer DEFAULT 100 NOT NULL,
    active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT uq_seller_locker_network UNIQUE (seller_id, channel_partner_id, locker_id)
);

CREATE INDEX IF NOT EXISTS ix_mcp_role_country ON marketplace_channel_partners (partner_role, country, active);
CREATE INDEX IF NOT EXISTS ix_seller_channel_listings_seller ON seller_channel_listings (seller_id, listing_status);
CREATE INDEX IF NOT EXISTS ix_seller_locker_network_seller ON seller_locker_network_links (seller_id, active);
