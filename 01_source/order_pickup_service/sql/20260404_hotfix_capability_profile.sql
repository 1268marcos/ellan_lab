BEGIN;

ALTER TABLE capability_profile
    ADD COLUMN IF NOT EXISTS valid_from TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS valid_until TIMESTAMPTZ;

-- índice que a migration espera
CREATE INDEX IF NOT EXISTS ix_cap_profile_active
    ON capability_profile (is_active, valid_from, valid_until);

COMMIT;