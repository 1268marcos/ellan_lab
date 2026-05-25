CREATE TABLE IF NOT EXISTS order_channel_partner_links (
    id VARCHAR(36) PRIMARY KEY,
    channel_id VARCHAR(36) NOT NULL,
    partner_id VARCHAR(36) NOT NULL,
    partner_kind VARCHAR(20) NOT NULL,
    link_role VARCHAR(30) DEFAULT 'PRIMARY' NOT NULL,
    active BOOLEAN DEFAULT true NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_opa_channel_links_channel ON order_channel_partner_links (channel_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_opa_channel_links_unique
    ON order_channel_partner_links (channel_id, partner_id, partner_kind);
