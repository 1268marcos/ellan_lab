BEGIN;

-- =========================================================
-- FIX 1 — USERS
-- =========================================================

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS locale VARCHAR(10),
    ADD COLUMN IF NOT EXISTS totp_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS totp_secret_ref VARCHAR(255);

-- índice opcional (útil futuramente)
CREATE INDEX IF NOT EXISTS ix_users_totp_enabled
    ON users (totp_enabled);

-- =========================================================
-- FIX 2 — PICKUP TOKENS
-- =========================================================

ALTER TABLE pickup_tokens
    ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE;

-- índice que estava quebrando
CREATE INDEX IF NOT EXISTS ix_pickup_tokens_active
    ON pickup_tokens (pickup_id, is_active)
    WHERE is_active = TRUE;

-- índice adicional útil
CREATE INDEX IF NOT EXISTS ix_pickup_tokens_active_only
    ON pickup_tokens (is_active);

COMMIT;