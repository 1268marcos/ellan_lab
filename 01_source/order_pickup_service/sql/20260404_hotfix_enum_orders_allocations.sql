-- =========================================================
-- 20260404_hotfix_enum_orders_allocations.sql
-- Fase 1: evoluir ENUM orderstatus
-- Fase 2: criar índice e alinhar allocations
-- =========================================================

-- =========================================================
-- FASE 1 — ENUM orderstatus
-- IMPORTANTE: sem BEGIN/COMMIT agrupando tudo
-- =========================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_enum
        WHERE enumlabel = 'CANCELLED'
          AND enumtypid = 'orderstatus'::regtype
    ) THEN
        ALTER TYPE orderstatus ADD VALUE 'CANCELLED';
    END IF;
END
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_enum
        WHERE enumlabel = 'REFUNDED'
          AND enumtypid = 'orderstatus'::regtype
    ) THEN
        ALTER TYPE orderstatus ADD VALUE 'REFUNDED';
    END IF;
END
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_enum
        WHERE enumlabel = 'EXPIRED'
          AND enumtypid = 'orderstatus'::regtype
    ) THEN
        ALTER TYPE orderstatus ADD VALUE 'EXPIRED';
    END IF;
END
$$;

-- =========================================================
-- FASE 2 — agora sim pode usar os novos valores
-- =========================================================

CREATE INDEX IF NOT EXISTS ix_orders_pickup_deadline
ON orders (pickup_deadline_at)
WHERE status NOT IN ('PICKED_UP', 'CANCELLED', 'REFUNDED', 'EXPIRED');

ALTER TABLE allocations
    ADD COLUMN IF NOT EXISTS allocated_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS released_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS release_reason VARCHAR(255),
    ADD COLUMN IF NOT EXISTS slot_size VARCHAR(20);

CREATE INDEX IF NOT EXISTS ix_allocations_allocated_at
    ON allocations (allocated_at);

CREATE INDEX IF NOT EXISTS ix_allocations_released_at
    ON allocations (released_at);