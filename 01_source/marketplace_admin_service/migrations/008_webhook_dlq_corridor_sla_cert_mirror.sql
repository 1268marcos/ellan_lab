-- Dead-letter, SLA por corredor, espelho certificações (marketplace)

ALTER TABLE marketplace_capability_webhook_deliveries ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'DELIVERED';
ALTER TABLE marketplace_capability_webhook_deliveries ADD COLUMN IF NOT EXISTS attempt_count INTEGER NOT NULL DEFAULT 1;
ALTER TABLE marketplace_capability_webhook_deliveries ADD COLUMN IF NOT EXISTS dead_lettered_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE marketplace_capability_webhook_deliveries ADD COLUMN IF NOT EXISTS replay_of_delivery_id VARCHAR(36);

CREATE INDEX IF NOT EXISTS ix_mkt_cap_wh_del_status ON marketplace_capability_webhook_deliveries(webhook_id, status, created_at DESC);

ALTER TABLE marketplace_player_certifications ADD COLUMN IF NOT EXISTS partner_certification_id VARCHAR(36);
ALTER TABLE marketplace_player_certifications ADD COLUMN IF NOT EXISTS source VARCHAR(32) NOT NULL DEFAULT 'SEED';

CREATE TABLE IF NOT EXISTS marketplace_corridor_sla (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    corridor_id VARCHAR(36) NOT NULL UNIQUE,
    corridor_code VARCHAR(48) NOT NULL,
    uptime_target_pct NUMERIC(5, 2) NOT NULL DEFAULT 99.50,
    on_time_delivery_pct NUMERIC(5, 2) NOT NULL DEFAULT 95.00,
    max_transit_hours INTEGER NOT NULL DEFAULT 72,
    webhook_p95_latency_ms INTEGER NOT NULL DEFAULT 2000,
    compliance_status VARCHAR(20) NOT NULL DEFAULT 'COMPLIANT',
    breach_count INTEGER NOT NULL DEFAULT 0,
    last_breach_at TIMESTAMP WITH TIME ZONE,
    notes TEXT,
    measured_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    FOREIGN KEY (corridor_id) REFERENCES marketplace_global_corridors(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_mkt_corridor_sla_code ON marketplace_corridor_sla(corridor_code, compliance_status);
