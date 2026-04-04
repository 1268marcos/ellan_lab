BEGIN;

-- =========================================================
-- 20260404_hotfix_users_orders.sql
-- Hotfix para alinhar users e orders com o schema exigido pelo código
-- =========================================================

-- ---------------------------------------------------------
-- USERS
-- ---------------------------------------------------------

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS anonymized_at TIMESTAMPTZ;

-- índice parcial usado pelo db_migrations.py
CREATE UNIQUE INDEX IF NOT EXISTS ux_users_email
    ON users (email)
    WHERE anonymized_at IS NULL;

-- ---------------------------------------------------------
-- ORDERS
-- colunas ausentes reportadas pelo _assert_required_schema()
-- ---------------------------------------------------------

ALTER TABLE orders
    ADD COLUMN IF NOT EXISTS site_id VARCHAR(100),
    ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(100),
    ADD COLUMN IF NOT EXISTS ecommerce_partner_id VARCHAR(100),
    ADD COLUMN IF NOT EXISTS partner_order_ref VARCHAR(255),
    ADD COLUMN IF NOT EXISTS sku_description TEXT,
    ADD COLUMN IF NOT EXISTS slot_size VARCHAR(20),
    ADD COLUMN IF NOT EXISTS card_last4 VARCHAR(8),
    ADD COLUMN IF NOT EXISTS card_brand VARCHAR(50),
    ADD COLUMN IF NOT EXISTS installments INTEGER,
    ADD COLUMN IF NOT EXISTS guest_name VARCHAR(255),
    ADD COLUMN IF NOT EXISTS consent_analytics BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS cancelled_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS cancel_reason VARCHAR(255),
    ADD COLUMN IF NOT EXISTS refunded_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS refund_reason VARCHAR(255);

-- ---------------------------------------------------------
-- Índices que o db.py espera em orders
-- (criados aqui por segurança)
-- ---------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_orders_status
    ON orders (status);

CREATE INDEX IF NOT EXISTS idx_orders_channel_status
    ON orders (channel, status);

CREATE INDEX IF NOT EXISTS idx_orders_region_status
    ON orders (region, status);

CREATE INDEX IF NOT EXISTS idx_orders_region_totem_status
    ON orders (region, totem_id, status);

CREATE INDEX IF NOT EXISTS idx_orders_region_totem_created_at
    ON orders (region, totem_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_orders_paid_at
    ON orders (paid_at);

CREATE INDEX IF NOT EXISTS idx_orders_picked_up_at
    ON orders (picked_up_at);

CREATE INDEX IF NOT EXISTS idx_orders_status_picked_up
    ON orders (status, picked_up_at);

CREATE INDEX IF NOT EXISTS idx_orders_totem_picked_up
    ON orders (totem_id, picked_up_at);

CREATE INDEX IF NOT EXISTS idx_orders_public_access_token_hash
    ON orders (public_access_token_hash);

CREATE INDEX IF NOT EXISTS ix_orders_user_id
    ON orders (user_id);

CREATE INDEX IF NOT EXISTS ix_orders_ecommerce_partner
    ON orders (ecommerce_partner_id);

CREATE INDEX IF NOT EXISTS ix_orders_pickup_deadline
    ON orders (pickup_deadline_at);

COMMIT;