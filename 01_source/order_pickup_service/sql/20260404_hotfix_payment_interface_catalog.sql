BEGIN;

-- =========================================================
-- FIX — compatibilidade com migration antiga
-- =========================================================

ALTER TABLE payment_interface_catalog
    ADD COLUMN IF NOT EXISTS requires_hw BOOLEAN NOT NULL DEFAULT FALSE;

-- índice opcional (pode ajudar filtros futuros)
CREATE INDEX IF NOT EXISTS ix_payment_interface_requires_hw
    ON payment_interface_catalog (requires_hw);

COMMIT;