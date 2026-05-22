-- Metadados de integracao por player (locker / marketplace / agregador)

ALTER TABLE marketplace_channel_partners ADD COLUMN IF NOT EXISTS parent_group character varying(32) DEFAULT 'MARKETPLACE';
ALTER TABLE marketplace_channel_partners ADD COLUMN IF NOT EXISTS integration_mode character varying(32) DEFAULT 'DIRECT_API';
ALTER TABLE marketplace_channel_partners ADD COLUMN IF NOT EXISTS regions_json text DEFAULT '[]';
ALTER TABLE marketplace_channel_partners ADD COLUMN IF NOT EXISTS api_docs_url character varying(500);

CREATE TABLE IF NOT EXISTS marketplace_channel_capabilities (
    id character varying(36) NOT NULL PRIMARY KEY,
    channel_partner_id character varying(36) NOT NULL,
    capability_code character varying(40) NOT NULL,
    protocol character varying(20) DEFAULT 'REST',
    direction character varying(10) DEFAULT 'INBOUND',
    enabled boolean DEFAULT true NOT NULL,
    notes text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT uq_channel_capability UNIQUE (channel_partner_id, capability_code)
);

CREATE INDEX IF NOT EXISTS ix_mcc_partner ON marketplace_channel_capabilities (channel_partner_id, enabled);
