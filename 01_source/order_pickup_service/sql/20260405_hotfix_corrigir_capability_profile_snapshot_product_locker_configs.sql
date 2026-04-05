-- ============================================================
-- HOTFIX COMPLETO - EXECUTAR NO POSTGRES_CENTRAL
-- Resolve: capability_profile_snapshot (status) e product_locker_configs
-- ============================================================

DO $$
BEGIN
    RAISE NOTICE '=== INICIANDO HOTFIX COMPLETO ===';

    -- ============================================================
    -- 1. CORREÇÃO DA TABELA capability_profile_snapshot
    -- ============================================================
    
    -- Criar tabela se não existir (com a coluna status desde o início)
    CREATE TABLE IF NOT EXISTS capability_profile_snapshot (
        id              BIGSERIAL    PRIMARY KEY,
        profile_id      BIGINT       NOT NULL,
        profile_code    VARCHAR(160) NOT NULL,
        locker_id       VARCHAR(36),
        resolved_json   JSONB        NOT NULL,
        snapshot_hash   VARCHAR(64)  NOT NULL,
        version         INTEGER      NOT NULL DEFAULT 1,
        status          VARCHAR(20)  NOT NULL DEFAULT 'DRAFT',
        published_at    TIMESTAMPTZ,
        superseded_at   TIMESTAMPTZ,
        generated_by    VARCHAR(100),
        created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
    );
    
    -- Adicionar coluna status se a tabela já existia (idempotente)
    BEGIN
        ALTER TABLE capability_profile_snapshot 
        ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'DRAFT';
    EXCEPTION WHEN duplicate_column THEN
        RAISE NOTICE 'Coluna status já existe em capability_profile_snapshot';
    END;
    
    -- Adicionar coluna published_at se não existir
    BEGIN
        ALTER TABLE capability_profile_snapshot 
        ADD COLUMN IF NOT EXISTS published_at TIMESTAMPTZ;
    EXCEPTION WHEN duplicate_column THEN
        RAISE NOTICE 'Coluna published_at já existe';
    END;
    
    -- Adicionar coluna superseded_at se não existir
    BEGIN
        ALTER TABLE capability_profile_snapshot 
        ADD COLUMN IF NOT EXISTS superseded_at TIMESTAMPTZ;
    EXCEPTION WHEN duplicate_column THEN
        RAISE NOTICE 'Coluna superseded_at já existe';
    END;
    
    -- Adicionar coluna generated_by se não existir
    BEGIN
        ALTER TABLE capability_profile_snapshot 
        ADD COLUMN IF NOT EXISTS generated_by VARCHAR(100);
    EXCEPTION WHEN duplicate_column THEN
        RAISE NOTICE 'Coluna generated_by já existe';
    END;
    
    -- Recriar índices (DROP IF EXISTS + CREATE)
    DROP INDEX IF EXISTS ix_cap_snapshot_profile_status;
    DROP INDEX IF EXISTS ix_cap_snapshot_locker;
    DROP INDEX IF EXISTS ix_cap_snapshot_code_status;
    
    CREATE INDEX IF NOT EXISTS ix_cap_snapshot_profile_status 
    ON capability_profile_snapshot (profile_id, status);
    
    CREATE INDEX IF NOT EXISTS ix_cap_snapshot_locker 
    ON capability_profile_snapshot (locker_id, status);
    
    CREATE INDEX IF NOT EXISTS ix_cap_snapshot_code_status 
    ON capability_profile_snapshot (profile_code, status);
    
    RAISE NOTICE '✓ capability_profile_snapshot corrigida';

    -- ============================================================
    -- 2. CORREÇÃO DA TABELA product_locker_configs
    -- ============================================================
    
    -- Adicionar todas as colunas faltantes de uma vez
    BEGIN
        ALTER TABLE product_locker_configs 
        ADD COLUMN IF NOT EXISTS min_value_cents BIGINT,
        ADD COLUMN IF NOT EXISTS max_value_cents BIGINT,
        ADD COLUMN IF NOT EXISTS max_weight_g INTEGER,
        ADD COLUMN IF NOT EXISTS max_width_mm INTEGER,
        ADD COLUMN IF NOT EXISTS max_height_mm INTEGER,
        ADD COLUMN IF NOT EXISTS max_depth_mm INTEGER,
        ADD COLUMN IF NOT EXISTS requires_id_check BOOLEAN NOT NULL DEFAULT FALSE;
    EXCEPTION WHEN others THEN
        RAISE NOTICE 'Erro ao adicionar colunas em product_locker_configs (podem já existir)';
    END;
    
    RAISE NOTICE '✓ product_locker_configs corrigida';

    -- ============================================================
    -- 3. CORREÇÃO DA TABELA orders (currency column)
    -- ============================================================
    
    BEGIN
        ALTER TABLE orders 
        ADD COLUMN IF NOT EXISTS currency VARCHAR(8) NOT NULL DEFAULT 'BRL';
    EXCEPTION WHEN duplicate_column THEN
        RAISE NOTICE 'Coluna currency já existe em orders';
    END;
    
    RAISE NOTICE '✓ orders corrigida';

    -- ============================================================
    -- 4. CORREÇÃO DA TABELA allocations (colunas faltantes)
    -- ============================================================
    
    BEGIN
        ALTER TABLE allocations 
        ADD COLUMN IF NOT EXISTS slot_size VARCHAR(8),
        ADD COLUMN IF NOT EXISTS allocated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        ADD COLUMN IF NOT EXISTS released_at TIMESTAMPTZ,
        ADD COLUMN IF NOT EXISTS release_reason VARCHAR(255);
    EXCEPTION WHEN others THEN
        RAISE NOTICE 'Erro ao adicionar colunas em allocations';
    END;
    
    RAISE NOTICE '✓ allocations corrigida';

    -- ============================================================
    -- 5. CORREÇÃO DA TABELA pickups (colunas faltantes)
    -- ============================================================
    
    BEGIN
        ALTER TABLE pickups 
        ADD COLUMN IF NOT EXISTS channel VARCHAR(10) NOT NULL DEFAULT 'KIOSK',
        ADD COLUMN IF NOT EXISTS region VARCHAR(10) NOT NULL DEFAULT 'SP',
        ADD COLUMN IF NOT EXISTS machine_id VARCHAR(100),
        ADD COLUMN IF NOT EXISTS operator_id VARCHAR(64),
        ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(100),
        ADD COLUMN IF NOT EXISTS site_id VARCHAR(100),
        ADD COLUMN IF NOT EXISTS lifecycle_stage VARCHAR(24) NOT NULL DEFAULT 'AWAITING_PAYMENT',
        ADD COLUMN IF NOT EXISTS ready_at TIMESTAMPTZ,
        ADD COLUMN IF NOT EXISTS door_opened_at TIMESTAMPTZ,
        ADD COLUMN IF NOT EXISTS item_removed_at TIMESTAMPTZ,
        ADD COLUMN IF NOT EXISTS door_closed_at TIMESTAMPTZ,
        ADD COLUMN IF NOT EXISTS redeemed_via VARCHAR(16),
        ADD COLUMN IF NOT EXISTS correlation_id VARCHAR(36),
        ADD COLUMN IF NOT EXISTS source_event_id VARCHAR(36),
        ADD COLUMN IF NOT EXISTS sensor_event_id VARCHAR(36),
        ADD COLUMN IF NOT EXISTS notes TEXT;
    EXCEPTION WHEN others THEN
        RAISE NOTICE 'Erro ao adicionar colunas em pickups';
    END;
    
    RAISE NOTICE '✓ pickups corrigida';

    -- ============================================================
    -- 6. CORREÇÃO DA TABELA pickup_tokens
    -- ============================================================
    
    BEGIN
        ALTER TABLE pickup_tokens 
        ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE;
    EXCEPTION WHEN duplicate_column THEN
        RAISE NOTICE 'Coluna is_active já existe em pickup_tokens';
    END;
    
    RAISE NOTICE '✓ pickup_tokens corrigida';

    -- ============================================================
    -- 7. CORREÇÃO DA TABELA notification_logs
    -- ============================================================
    
    BEGIN
        ALTER TABLE notification_logs 
        ADD COLUMN IF NOT EXISTS pickup_id VARCHAR(36),
        ADD COLUMN IF NOT EXISTS delivery_id VARCHAR(36),
        ADD COLUMN IF NOT EXISTS rental_id VARCHAR(36),
        ADD COLUMN IF NOT EXISTS provider_status VARCHAR(100),
        ADD COLUMN IF NOT EXISTS error_detail TEXT,
        ADD COLUMN IF NOT EXISTS locale VARCHAR(10) NOT NULL DEFAULT 'pt-BR';
    EXCEPTION WHEN others THEN
        RAISE NOTICE 'Erro ao adicionar colunas em notification_logs';
    END;
    
    -- Recriar índices de notification_logs
    DROP INDEX IF EXISTS ix_notif_pickup;
    DROP INDEX IF EXISTS ix_notif_delivery;
    CREATE INDEX IF NOT EXISTS ix_notif_pickup ON notification_logs (pickup_id);
    CREATE INDEX IF NOT EXISTS ix_notif_delivery ON notification_logs (delivery_id);
    
    RAISE NOTICE '✓ notification_logs corrigida';

    -- ============================================================
    -- 8. LIMPAR MIGRAÇÃO FALHA (permite re-execução)
    -- ============================================================
    
    DELETE FROM schema_migrations 
    WHERE name = 'capability_profile_snapshot.create_table_v1';
    
    DELETE FROM schema_migrations 
    WHERE name = 'schema.auto_heal_legacy_v1';
    
    RAISE NOTICE '✓ Migrations falhas removidas';

    -- ============================================================
    -- 9. VERIFICAR SE AS FK EXISTEM (adicionar se faltarem)
    -- ============================================================
    
    -- Adicionar FK para profile_id se não existir
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.table_constraints 
            WHERE constraint_name = 'fk_cap_snapshot_profile'
            AND table_name = 'capability_profile_snapshot'
        ) THEN
            ALTER TABLE capability_profile_snapshot 
            ADD CONSTRAINT fk_cap_snapshot_profile 
            FOREIGN KEY (profile_id) REFERENCES capability_profile(id);
        END IF;
    EXCEPTION WHEN others THEN
        RAISE NOTICE 'FK para profile_id pode já existir ou tabela capability_profile não existe';
    END;
    
    -- Adicionar FK para locker_id se não existir
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.table_constraints 
            WHERE constraint_name = 'fk_cap_snapshot_locker'
            AND table_name = 'capability_profile_snapshot'
        ) THEN
            ALTER TABLE capability_profile_snapshot 
            ADD CONSTRAINT fk_cap_snapshot_locker 
            FOREIGN KEY (locker_id) REFERENCES lockers(id);
        END IF;
    EXCEPTION WHEN others THEN
        RAISE NOTICE 'FK para locker_id pode já existir ou tabela lockers não existe';
    END;
    
    RAISE NOTICE '=== HOTFIX CONCLUÍDO COM SUCESSO ===';
END $$;

-- ============================================================
-- VERIFICAÇÃO FINAL
-- ============================================================

SELECT '✅ capability_profile_snapshot.status existe: ' || 
       CASE WHEN EXISTS (
           SELECT 1 FROM information_schema.columns 
           WHERE table_name = 'capability_profile_snapshot' AND column_name = 'status'
       ) THEN 'SIM' ELSE 'NÃO' END AS check1;

SELECT '✅ product_locker_configs.requires_id_check existe: ' || 
       CASE WHEN EXISTS (
           SELECT 1 FROM information_schema.columns 
           WHERE table_name = 'product_locker_configs' AND column_name = 'requires_id_check'
       ) THEN 'SIM' ELSE 'NÃO' END AS check2;

SELECT '✅ orders.currency existe: ' || 
       CASE WHEN EXISTS (
           SELECT 1 FROM information_schema.columns 
           WHERE table_name = 'orders' AND column_name = 'currency'
       ) THEN 'SIM' ELSE 'NÃO' END AS check3;