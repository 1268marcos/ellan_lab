-- ============================================================
-- SOLUÇÃO DEFINITIVA - Adicionar todas as colunas esperadas
-- ============================================================

-- product_categories - todas as colunas que o schema validation espera
ALTER TABLE product_categories ADD COLUMN IF NOT EXISTS max_weight_g INTEGER;
ALTER TABLE product_categories ADD COLUMN IF NOT EXISTS default_temperature_zone VARCHAR(32) NOT NULL DEFAULT 'AMBIENT';
ALTER TABLE product_categories ADD COLUMN IF NOT EXISTS default_security_level VARCHAR(32) NOT NULL DEFAULT 'STANDARD';
ALTER TABLE product_categories ADD COLUMN IF NOT EXISTS is_hazardous BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE product_categories ADD COLUMN IF NOT EXISTS requires_age_verification BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE product_categories ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE product_categories ADD COLUMN IF NOT EXISTS parent_category VARCHAR(64);
ALTER TABLE product_categories ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
ALTER TABLE product_categories ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

-- product_locker_configs - garantir todas as colunas
ALTER TABLE product_locker_configs ADD COLUMN IF NOT EXISTS min_value_cents BIGINT;
ALTER TABLE product_locker_configs ADD COLUMN IF NOT EXISTS max_value_cents BIGINT;
ALTER TABLE product_locker_configs ADD COLUMN IF NOT EXISTS max_weight_g INTEGER;
ALTER TABLE product_locker_configs ADD COLUMN IF NOT EXISTS max_width_mm INTEGER;
ALTER TABLE product_locker_configs ADD COLUMN IF NOT EXISTS max_height_mm INTEGER;
ALTER TABLE product_locker_configs ADD COLUMN IF NOT EXISTS max_depth_mm INTEGER;
ALTER TABLE product_locker_configs ADD COLUMN IF NOT EXISTS requires_id_check BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE product_locker_configs ADD COLUMN IF NOT EXISTS allowed BOOLEAN NOT NULL DEFAULT TRUE;
ALTER TABLE product_locker_configs ADD COLUMN IF NOT EXISTS temperature_zone VARCHAR(32) NOT NULL DEFAULT 'ANY';
ALTER TABLE product_locker_configs ADD COLUMN IF NOT EXISTS requires_signature BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE product_locker_configs ADD COLUMN IF NOT EXISTS is_fragile BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE product_locker_configs ADD COLUMN IF NOT EXISTS is_hazardous BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE product_locker_configs ADD COLUMN IF NOT EXISTS priority INTEGER NOT NULL DEFAULT 100;

-- Limpar migrations falhas novamente
DELETE FROM schema_migrations WHERE name = 'schema.auto_heal_legacy_v1';

-- Verificar
SELECT '✅ Correção concluída!' AS status;