BEGIN;

-- =========================================================
-- DIMENSÕES FÍSICAS DOS SLOTS
-- =========================================================

ALTER TABLE locker_slot_configs
    ADD COLUMN IF NOT EXISTS width_mm INTEGER,
    ADD COLUMN IF NOT EXISTS height_mm INTEGER,
    ADD COLUMN IF NOT EXISTS depth_mm INTEGER,
    ADD COLUMN IF NOT EXISTS max_weight_g INTEGER;

-- =========================================================
-- CHECKS (boas práticas industriais)
-- =========================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'ck_slot_cfg_dimensions_positive'
    ) THEN
        ALTER TABLE locker_slot_configs
        ADD CONSTRAINT ck_slot_cfg_dimensions_positive
        CHECK (
            (width_mm IS NULL OR width_mm > 0) AND
            (height_mm IS NULL OR height_mm > 0) AND
            (depth_mm IS NULL OR depth_mm > 0) AND
            (max_weight_g IS NULL OR max_weight_g > 0)
        );
    END IF;
END
$$;

-- =========================================================
-- ÍNDICES ÚTEIS PARA MATCH DE SKU
-- =========================================================

CREATE INDEX IF NOT EXISTS ix_slot_cfg_dimensions
ON locker_slot_configs (locker_id, slot_size, width_mm, height_mm, depth_mm);

COMMIT;