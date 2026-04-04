BEGIN;

-- =========================================================
-- FIX — compatibilidade com migration antiga
-- =========================================================

ALTER TABLE payment_method_catalog
    ADD COLUMN IF NOT EXISTS is_instant BOOLEAN NOT NULL DEFAULT FALSE;

-- índice opcional
CREATE INDEX IF NOT EXISTS ix_payment_method_catalog_is_instant
    ON payment_method_catalog (is_instant);

COMMIT;