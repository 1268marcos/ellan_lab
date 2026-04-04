BEGIN;

-- =========================================================
-- 20260404_hotfix_lockers_order_items.sql
-- Hotfix:
--   1) lockers -> campos operacionais de localização e política de retirada
--   2) order_items -> base para pedidos com múltiplos SKUs
-- =========================================================

-- =========================================================
-- BLOCO 1 — LOCKERS
-- =========================================================

ALTER TABLE lockers
    ADD COLUMN IF NOT EXISTS finding_instructions TEXT,
    ADD COLUMN IF NOT EXISTS pickup_code_length INTEGER NOT NULL DEFAULT 6,
    ADD COLUMN IF NOT EXISTS pickup_reuse_policy VARCHAR(32) NOT NULL DEFAULT 'NO_REUSE',
    ADD COLUMN IF NOT EXISTS pickup_reuse_window_sec INTEGER,
    ADD COLUMN IF NOT EXISTS pickup_max_reopens INTEGER NOT NULL DEFAULT 0;

-- Checks básicos de integridade
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_lockers_pickup_code_length_range'
    ) THEN
        ALTER TABLE lockers
            ADD CONSTRAINT ck_lockers_pickup_code_length_range
            CHECK (pickup_code_length BETWEEN 4 AND 12);
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_lockers_pickup_reuse_policy'
    ) THEN
        ALTER TABLE lockers
            ADD CONSTRAINT ck_lockers_pickup_reuse_policy
            CHECK (
                pickup_reuse_policy IN (
                    'NO_REUSE',
                    'SAME_TOKEN_UNTIL_DEADLINE',
                    'ALLOW_REOPEN_WINDOW'
                )
            );
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_lockers_pickup_reuse_window_sec_non_negative'
    ) THEN
        ALTER TABLE lockers
            ADD CONSTRAINT ck_lockers_pickup_reuse_window_sec_non_negative
            CHECK (
                pickup_reuse_window_sec IS NULL
                OR pickup_reuse_window_sec >= 0
            );
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_lockers_pickup_max_reopens_non_negative'
    ) THEN
        ALTER TABLE lockers
            ADD CONSTRAINT ck_lockers_pickup_max_reopens_non_negative
            CHECK (pickup_max_reopens >= 0);
    END IF;
END
$$;

-- Índices úteis
CREATE INDEX IF NOT EXISTS ix_lockers_pickup_code_length
    ON lockers (pickup_code_length);

CREATE INDEX IF NOT EXISTS ix_lockers_pickup_reuse_policy
    ON lockers (pickup_reuse_policy);


-- =========================================================
-- BLOCO 2 — ORDER ITEMS
-- =========================================================

CREATE TABLE IF NOT EXISTS order_items (
    id                  BIGSERIAL PRIMARY KEY,
    order_id            VARCHAR(36) NOT NULL REFERENCES orders(id) ON DELETE CASCADE,

    -- SKU / catálogo
    sku_id              VARCHAR(255) NOT NULL,
    sku_description     TEXT,

    -- Quantidade e preço
    quantity            INTEGER NOT NULL DEFAULT 1,
    unit_amount_cents   BIGINT NOT NULL,
    total_amount_cents  BIGINT NOT NULL,

    -- Operação física / fulfillment
    slot_preference     INTEGER,
    slot_size           VARCHAR(20),

    -- Ciclo de vida do item dentro do pedido
    item_status         VARCHAR(32) NOT NULL DEFAULT 'PENDING',

    -- Metadados livres
    metadata_json       JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Checks básicos
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_order_items_quantity_positive'
    ) THEN
        ALTER TABLE order_items
            ADD CONSTRAINT ck_order_items_quantity_positive
            CHECK (quantity > 0);
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_order_items_unit_amount_non_negative'
    ) THEN
        ALTER TABLE order_items
            ADD CONSTRAINT ck_order_items_unit_amount_non_negative
            CHECK (unit_amount_cents >= 0);
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_order_items_total_amount_non_negative'
    ) THEN
        ALTER TABLE order_items
            ADD CONSTRAINT ck_order_items_total_amount_non_negative
            CHECK (total_amount_cents >= 0);
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_order_items_total_matches_quantity'
    ) THEN
        ALTER TABLE order_items
            ADD CONSTRAINT ck_order_items_total_matches_quantity
            CHECK (total_amount_cents = quantity * unit_amount_cents);
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_order_items_slot_preference_positive'
    ) THEN
        ALTER TABLE order_items
            ADD CONSTRAINT ck_order_items_slot_preference_positive
            CHECK (slot_preference IS NULL OR slot_preference > 0);
    END IF;
END
$$;

-- Índices
CREATE INDEX IF NOT EXISTS ix_order_items_order_id
    ON order_items (order_id);

CREATE INDEX IF NOT EXISTS ix_order_items_sku_id
    ON order_items (sku_id);

CREATE INDEX IF NOT EXISTS ix_order_items_item_status
    ON order_items (item_status);

CREATE INDEX IF NOT EXISTS ix_order_items_order_status
    ON order_items (order_id, item_status);

CREATE INDEX IF NOT EXISTS ix_order_items_slot_preference
    ON order_items (slot_preference);

CREATE INDEX IF NOT EXISTS ix_order_items_slot_size
    ON order_items (slot_size);


-- =========================================================
-- BLOCO 3 — BACKFILL COMPATÍVEL
-- Cria 1 item por pedido existente que ainda não tenha item
-- usando o modelo legado atual de orders.sku_id
-- =========================================================

INSERT INTO order_items (
    order_id,
    sku_id,
    sku_description,
    quantity,
    unit_amount_cents,
    total_amount_cents,
    slot_size,
    item_status,
    metadata_json
)
SELECT
    o.id,
    COALESCE(o.sku_id, 'UNKNOWN_SKU'),
    o.sku_description,
    1,
    COALESCE(o.amount_cents, 0),
    COALESCE(o.amount_cents, 0),
    o.slot_size,
    CASE
        WHEN o.status IS NULL THEN 'PENDING'
        ELSE o.status::text
    END,
    jsonb_build_object(
        'migrated_from_orders_table', true,
        'source', '20260404_hotfix_lockers_order_items'
    )
FROM orders o
WHERE NOT EXISTS (
    SELECT 1
    FROM order_items oi
    WHERE oi.order_id = o.id
);

COMMIT;