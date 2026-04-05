BEGIN;

-- =========================================================
-- GEOLOCALIZAÇÃO
-- =========================================================

ALTER TABLE lockers
    ADD COLUMN IF NOT EXISTS geolocation_wkt TEXT;

-- =========================================================
-- CAPACIDADES DE HARDWARE
-- =========================================================

ALTER TABLE lockers
    ADD COLUMN IF NOT EXISTS has_card_reader BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS has_kiosk BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS has_nfc BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS has_printer BOOLEAN NOT NULL DEFAULT FALSE;

-- =========================================================
-- DISPONIBILIDADE
-- =========================================================

ALTER TABLE lockers
    ADD COLUMN IF NOT EXISTS slots_available INTEGER NOT NULL DEFAULT 0;

-- =========================================================
-- CHECKS
-- =========================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'ck_lockers_slots_available_non_negative'
    ) THEN
        ALTER TABLE lockers
            ADD CONSTRAINT ck_lockers_slots_available_non_negative
            CHECK (slots_available >= 0);
    END IF;
END
$$;

-- =========================================================
-- ÍNDICES
-- =========================================================

CREATE INDEX IF NOT EXISTS ix_lockers_has_kiosk
    ON lockers (has_kiosk);

CREATE INDEX IF NOT EXISTS ix_lockers_has_nfc
    ON lockers (has_nfc);

CREATE INDEX IF NOT EXISTS ix_lockers_slots_available
    ON lockers (slots_available);

COMMIT;