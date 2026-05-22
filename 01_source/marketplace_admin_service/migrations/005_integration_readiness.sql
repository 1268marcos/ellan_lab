-- Prontidao de integracao global (scores, incidentes, auditoria)

CREATE TABLE IF NOT EXISTS marketplace_integration_readiness (
    channel_partner_id character varying(36) NOT NULL PRIMARY KEY,
    partner_code character varying(48) NOT NULL,
    score_total numeric(5, 2) NOT NULL DEFAULT 0,
    score_capabilities numeric(5, 2) NOT NULL DEFAULT 0,
    score_api numeric(5, 2) NOT NULL DEFAULT 0,
    score_operations numeric(5, 2) NOT NULL DEFAULT 0,
    readiness_band character varying(16) NOT NULL DEFAULT 'PLANNED',
    blockers_json text NOT NULL DEFAULT '[]',
    ml_network_code character varying(48),
    computed_at timestamp with time zone NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_mkt_readiness_band ON marketplace_integration_readiness (readiness_band, score_total DESC);
CREATE INDEX IF NOT EXISTS ix_mkt_readiness_code ON marketplace_integration_readiness (partner_code);

CREATE TABLE IF NOT EXISTS marketplace_integration_incidents (
    id character varying(36) NOT NULL PRIMARY KEY,
    channel_partner_id character varying(36) NOT NULL,
    partner_code character varying(48) NOT NULL,
    severity character varying(16) NOT NULL DEFAULT 'WARNING',
    incident_type character varying(32) NOT NULL DEFAULT 'API_DEGRADED',
    title character varying(200) NOT NULL,
    status character varying(20) NOT NULL DEFAULT 'OPEN',
    details_json text NOT NULL DEFAULT '{}',
    opened_at timestamp with time zone NOT NULL DEFAULT now(),
    resolved_at timestamp with time zone
);

CREATE INDEX IF NOT EXISTS ix_mkt_incidents_open ON marketplace_integration_incidents (status, severity);

CREATE TABLE IF NOT EXISTS marketplace_sync_audit_log (
    id character varying(36) NOT NULL PRIMARY KEY,
    event_type character varying(40) NOT NULL,
    entity_type character varying(32) NOT NULL,
    entity_id character varying(48),
    actor_id character varying(64),
    summary character varying(255) NOT NULL,
    payload_json text NOT NULL DEFAULT '{}',
    created_at timestamp with time zone NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_mkt_audit_created ON marketplace_sync_audit_log (created_at DESC);
