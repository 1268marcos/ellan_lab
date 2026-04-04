BEGIN;

-- =========================================================
-- FIX — notification_logs
-- =========================================================

ALTER TABLE notification_logs
    ADD COLUMN IF NOT EXISTS pickup_id UUID,
    ADD COLUMN IF NOT EXISTS delivery_id UUID,
    ADD COLUMN IF NOT EXISTS rental_id UUID,
    ADD COLUMN IF NOT EXISTS provider_status VARCHAR(100),
    ADD COLUMN IF NOT EXISTS error_detail TEXT,
    ADD COLUMN IF NOT EXISTS locale VARCHAR(10);

-- =========================================================
-- ÍNDICES esperados pelo sistema
-- =========================================================

CREATE INDEX IF NOT EXISTS ix_notif_pickup
    ON notification_logs (pickup_id);

CREATE INDEX IF NOT EXISTS ix_notif_delivery
    ON notification_logs (delivery_id);

CREATE INDEX IF NOT EXISTS ix_notif_rental
    ON notification_logs (rental_id);

CREATE INDEX IF NOT EXISTS ix_notif_provider_status
    ON notification_logs (provider_status);

COMMIT;