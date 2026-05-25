-- payload para push/pull runtime reconcile
ALTER TABLE hardware_sync_queue ADD COLUMN IF NOT EXISTS payload_json JSON NOT NULL DEFAULT '{}';
