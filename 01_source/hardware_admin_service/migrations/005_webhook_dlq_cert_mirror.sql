-- Webhook DLQ columns + cert mirror metadata

ALTER TABLE hardware_capability_webhooks ADD COLUMN IF NOT EXISTS secret_key VARCHAR(256);

ALTER TABLE hardware_player_certifications ADD COLUMN IF NOT EXISTS source VARCHAR(32) NOT NULL DEFAULT 'SEED';
ALTER TABLE hardware_player_certifications ADD COLUMN IF NOT EXISTS marketplace_cert_id VARCHAR(36);

CREATE INDEX IF NOT EXISTS ix_hw_cert_mirror ON hardware_player_certifications (marketplace_cert_id);
CREATE INDEX IF NOT EXISTS ix_hw_cert_source ON hardware_player_certifications (source, player_code);

CREATE INDEX IF NOT EXISTS ix_hw_webhook_delivery_status ON hardware_capability_webhook_deliveries (status, webhook_id);
