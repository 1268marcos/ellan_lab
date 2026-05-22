-- Alertas automaticos de queda de score + webhooks reais por capability

CREATE TABLE IF NOT EXISTS marketplace_readiness_score_history (
    id character varying(36) NOT NULL PRIMARY KEY,
    channel_partner_id character varying(36) NOT NULL,
    partner_code character varying(48) NOT NULL,
    score_total numeric(5, 2) NOT NULL,
    readiness_band character varying(16) NOT NULL,
    recorded_at timestamp with time zone NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_mkt_score_hist_partner ON marketplace_readiness_score_history (channel_partner_id, recorded_at DESC);

CREATE TABLE IF NOT EXISTS marketplace_readiness_alerts (
    id character varying(36) NOT NULL PRIMARY KEY,
    channel_partner_id character varying(36) NOT NULL,
    partner_code character varying(48) NOT NULL,
    alert_type character varying(32) NOT NULL DEFAULT 'SCORE_DROP',
    severity character varying(16) NOT NULL DEFAULT 'WARNING',
    previous_score numeric(5, 2),
    new_score numeric(5, 2) NOT NULL,
    score_delta numeric(5, 2) NOT NULL,
    previous_band character varying(16),
    new_band character varying(16) NOT NULL,
    status character varying(20) NOT NULL DEFAULT 'OPEN',
    webhook_dispatched boolean NOT NULL DEFAULT false,
    details_json text NOT NULL DEFAULT '{}',
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    acknowledged_at timestamp with time zone
);

CREATE INDEX IF NOT EXISTS ix_mkt_readiness_alerts_open ON marketplace_readiness_alerts (status, created_at DESC);

CREATE TABLE IF NOT EXISTS marketplace_capability_webhooks (
    id character varying(36) NOT NULL PRIMARY KEY,
    channel_partner_id character varying(36) NOT NULL,
    partner_code character varying(48) NOT NULL,
    capability_code character varying(40) NOT NULL,
    url character varying(500) NOT NULL,
    secret_hash character varying(128) NOT NULL,
    secret_key character varying(256),
    event_types_json text NOT NULL DEFAULT '["readiness.score_drop","capability.health"]',
    active boolean NOT NULL DEFAULT true,
    last_http_status integer,
    last_delivered_at timestamp with time zone,
    last_error text,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    CONSTRAINT uq_mkt_cap_webhook UNIQUE (channel_partner_id, capability_code)
);

CREATE INDEX IF NOT EXISTS ix_mkt_cap_webhook_partner ON marketplace_capability_webhooks (channel_partner_id, active);

CREATE TABLE IF NOT EXISTS marketplace_capability_webhook_deliveries (
    id character varying(36) NOT NULL PRIMARY KEY,
    webhook_id character varying(36) NOT NULL REFERENCES marketplace_capability_webhooks(id) ON DELETE CASCADE,
    event_type character varying(48) NOT NULL,
    payload_json text NOT NULL,
    http_status integer,
    success boolean NOT NULL DEFAULT false,
    response_snippet text,
    created_at timestamp with time zone NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_mkt_cap_wh_del_webhook ON marketplace_capability_webhook_deliveries (webhook_id, created_at DESC);
