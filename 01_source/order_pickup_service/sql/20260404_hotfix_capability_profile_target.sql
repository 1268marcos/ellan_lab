BEGIN;

ALTER TABLE capability_profile_target
    ADD COLUMN IF NOT EXISTS locker_id VARCHAR(64);

CREATE INDEX IF NOT EXISTS ix_cpt_locker_id
    ON capability_profile_target (locker_id);

COMMIT;