-- Webhooks reais por capability (espelho marketplace_capability_webhooks)

CREATE TABLE IF NOT EXISTS partner_capability_webhooks (
    id character varying(36) NOT NULL PRIMARY KEY,
    ecosystem_player_id character varying(36) NOT NULL REFERENCES partner_ecosystem_players(id) ON DELETE CASCADE,
    player_code character varying(48) NOT NULL,
    capability_code character varying(40) NOT NULL,
    url character varying(500) NOT NULL,
    secret_hash character varying(128) NOT NULL,
    secret_key character varying(256),
    event_types_json text NOT NULL DEFAULT '["capability.health","webhook.test"]',
    source character varying(32) NOT NULL DEFAULT 'SEED',
    marketplace_webhook_id character varying(36),
    active boolean NOT NULL DEFAULT true,
    last_http_status integer,
    last_delivered_at timestamp with time zone,
    last_error text,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    CONSTRAINT uq_partner_cap_webhook UNIQUE (ecosystem_player_id, capability_code)
);

CREATE INDEX IF NOT EXISTS ix_partner_cap_webhook_player ON partner_capability_webhooks (ecosystem_player_id, active);
CREATE INDEX IF NOT EXISTS ix_partner_cap_webhook_code ON partner_capability_webhooks (player_code, capability_code);

CREATE TABLE IF NOT EXISTS partner_capability_webhook_deliveries (
    id character varying(36) NOT NULL PRIMARY KEY,
    webhook_id character varying(36) NOT NULL REFERENCES partner_capability_webhooks(id) ON DELETE CASCADE,
    event_type character varying(48) NOT NULL,
    payload_json text NOT NULL,
    http_status integer,
    success boolean NOT NULL DEFAULT false,
    response_snippet text,
    created_at timestamp with time zone NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_partner_cap_wh_del ON partner_capability_webhook_deliveries (webhook_id, created_at DESC);
