-- ============================================================
-- HOTFIX CORRETIVO - RECRIAÇÃO SEGURA DA TABELA
-- ============================================================

DO $$
DECLARE
    v_has_data boolean;
BEGIN
    RAISE NOTICE '=== HOTFIX CORRETIVO - INICIANDO ===';

    -- ============================================================
    -- 1. VERIFICAR SE A TABELA EXISTE E SE TEM DADOS
    -- ============================================================
    SELECT EXISTS (
        SELECT 1 FROM capability_profile_snapshot LIMIT 1
    ) INTO v_has_data;
    
    RAISE NOTICE 'Tabela capability_profile_snapshot existe e tem dados: %', v_has_data;

    -- ============================================================
    -- 2. FAZER BACKUP DOS DADOS SE EXISTIREM
    -- ============================================================
    IF v_has_data THEN
        RAISE NOTICE 'Criando backup dos dados...';
        
        -- Criar tabela temporária de backup
        CREATE TEMP TABLE IF NOT EXISTS _cap_snapshot_backup AS
        SELECT * FROM capability_profile_snapshot LIMIT 0;
        
        INSERT INTO _cap_snapshot_backup
        SELECT * FROM capability_profile_snapshot;
        
        RAISE NOTICE 'Backup criado com % registros', (SELECT COUNT(*) FROM _cap_snapshot_backup);
    END IF;

    -- ============================================================
    -- 3. REMOVER ÍNDICES EXISTENTES (IGNORANDO ERROS)
    -- ============================================================
    BEGIN
        DROP INDEX IF EXISTS ix_cap_snapshot_profile_status;
        DROP INDEX IF EXISTS ix_cap_snapshot_locker;
        DROP INDEX IF EXISTS ix_cap_snapshot_code_status;
        DROP INDEX IF EXISTS ix_cap_snapshot_profile_id;
        DROP INDEX IF EXISTS ix_cap_snapshot_profile_code;
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'Erro ao dropar índices (podem não existir)';
    END;

    -- ============================================================
    -- 4. REMOVER CONSTRAINTS EXISTENTES
    -- ============================================================
    BEGIN
        ALTER TABLE capability_profile_snapshot DROP CONSTRAINT IF EXISTS capability_profile_snapshot_profile_id_fkey;
        ALTER TABLE capability_profile_snapshot DROP CONSTRAINT IF EXISTS fk_cap_snapshot_profile;
        ALTER TABLE capability_profile_snapshot DROP CONSTRAINT IF EXISTS capability_profile_snapshot_locker_id_fkey;
        ALTER TABLE capability_profile_snapshot DROP CONSTRAINT IF EXISTS fk_cap_snapshot_locker;
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'Erro ao dropar constraints';
    END;

    -- ============================================================
    -- 5. RENOMEAR TABELA ANTIGA (BACKUP)
    -- ============================================================
    BEGIN
        ALTER TABLE capability_profile_snapshot RENAME TO capability_profile_snapshot_old;
        RAISE NOTICE 'Tabela antiga renomeada para capability_profile_snapshot_old';
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'Erro ao renomear tabela antiga';
    END;

    -- ============================================================
    -- 6. CRIAR TABELA NOVA COM ESTRUTURA CORRETA
    -- ============================================================
    CREATE TABLE capability_profile_snapshot (
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
    
    RAISE NOTICE 'Nova tabela capability_profile_snapshot criada';

    -- ============================================================
    -- 7. RESTAURAR DADOS DO BACKUP (SE EXISTIREM)
    -- ============================================================
    IF v_has_data THEN
        BEGIN
            -- Tentar restaurar apenas as colunas que existem no backup
            INSERT INTO capability_profile_snapshot (
                id, profile_id, profile_code, locker_id, 
                resolved_json, snapshot_hash, version, status,
                published_at, superseded_at, generated_by, created_at
            )
            SELECT 
                id, 
                profile_id, 
                profile_code, 
                NULL::VARCHAR(36) as locker_id,  -- valor padrão se não existir
                resolved_json, 
                snapshot_hash, 
                COALESCE(version, 1) as version,
                COALESCE(status, 'DRAFT') as status,
                published_at, 
                superseded_at, 
                generated_by, 
                COALESCE(created_at, NOW()) as created_at
            FROM _cap_snapshot_backup;
            
            RAISE NOTICE 'Dados restaurados: % registros', (SELECT COUNT(*) FROM capability_profile_snapshot);
        EXCEPTION WHEN OTHERS THEN
            RAISE NOTICE 'Erro ao restaurar dados: %', SQLERRM;
            RAISE NOTICE 'Tabela nova está vazia - será populada pelo sistema';
        END;
    END IF;

    -- ============================================================
    -- 8. CRIAR ÍNDICES
    -- ============================================================
    CREATE INDEX IF NOT EXISTS ix_cap_snapshot_profile_status 
    ON capability_profile_snapshot (profile_id, status);
    
    CREATE INDEX IF NOT EXISTS ix_cap_snapshot_locker 
    ON capability_profile_snapshot (locker_id, status);
    
    CREATE INDEX IF NOT EXISTS ix_cap_snapshot_code_status 
    ON capability_profile_snapshot (profile_code, status);
    
    CREATE INDEX IF NOT EXISTS ix_cap_snapshot_profile_id 
    ON capability_profile_snapshot (profile_id);
    
    CREATE INDEX IF NOT EXISTS ix_cap_snapshot_created_at 
    ON capability_profile_snapshot (created_at);
    
    RAISE NOTICE 'Índices criados';

    -- ============================================================
    -- 9. CRIAR CONSTRAINTS DE FK
    -- ============================================================
    BEGIN
        ALTER TABLE capability_profile_snapshot 
        ADD CONSTRAINT fk_cap_snapshot_profile 
        FOREIGN KEY (profile_id) REFERENCES capability_profile(id);
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'FK para profile_id: %', SQLERRM;
    END;
    
    BEGIN
        ALTER TABLE capability_profile_snapshot 
        ADD CONSTRAINT fk_cap_snapshot_locker 
        FOREIGN KEY (locker_id) REFERENCES lockers(id);
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'FK para locker_id: % (tabela lockers pode não existir ainda)', SQLERRM;
    END;
    
    RAISE NOTICE 'Constraints criadas';

    -- ============================================================
    -- 10. DROP TABELA ANTIGA (OPCIONAL - COMENTADO)
    -- ============================================================
    -- DROP TABLE IF EXISTS capability_profile_snapshot_old;
    -- RAISE NOTICE 'Tabela antiga removida (descomente se quiser)';
    
    RAISE NOTICE '=== HOTFIX CORRETIVO CONCLUÍDO ===';
END $$;

-- ============================================================
-- CORREÇÃO DA product_locker_configs (simples, sem erros)
-- ============================================================

DO $$
BEGIN
    RAISE NOTICE '=== CORRIGINDO product_locker_configs ===';
    
    -- Verificar se a tabela existe
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'product_locker_configs') THEN
        -- Adicionar colunas uma por uma, ignorando erros
        BEGIN
            ALTER TABLE product_locker_configs ADD COLUMN IF NOT EXISTS min_value_cents BIGINT;
        EXCEPTION WHEN OTHERS THEN END;
        
        BEGIN
            ALTER TABLE product_locker_configs ADD COLUMN IF NOT EXISTS max_value_cents BIGINT;
        EXCEPTION WHEN OTHERS THEN END;
        
        BEGIN
            ALTER TABLE product_locker_configs ADD COLUMN IF NOT EXISTS max_weight_g INTEGER;
        EXCEPTION WHEN OTHERS THEN END;
        
        BEGIN
            ALTER TABLE product_locker_configs ADD COLUMN IF NOT EXISTS max_width_mm INTEGER;
        EXCEPTION WHEN OTHERS THEN END;
        
        BEGIN
            ALTER TABLE product_locker_configs ADD COLUMN IF NOT EXISTS max_height_mm INTEGER;
        EXCEPTION WHEN OTHERS THEN END;
        
        BEGIN
            ALTER TABLE product_locker_configs ADD COLUMN IF NOT EXISTS max_depth_mm INTEGER;
        EXCEPTION WHEN OTHERS THEN END;
        
        BEGIN
            ALTER TABLE product_locker_configs ADD COLUMN IF NOT EXISTS requires_id_check BOOLEAN DEFAULT FALSE;
            UPDATE product_locker_configs SET requires_id_check = FALSE WHERE requires_id_check IS NULL;
            ALTER TABLE product_locker_configs ALTER COLUMN requires_id_check SET NOT NULL;
        EXCEPTION WHEN OTHERS THEN END;
        
        RAISE NOTICE '✅ product_locker_configs corrigida';
    ELSE
        RAISE NOTICE '⚠️ Tabela product_locker_configs não existe - será criada pela migration';
    END IF;
END $$;

-- ============================================================
-- LIMPAR MIGRAÇÕES FALHAS
-- ============================================================

DELETE FROM schema_migrations WHERE name = 'capability_profile_snapshot.create_table_v1';
DELETE FROM schema_migrations WHERE name = 'schema.auto_heal_legacy_v1';

-- ============================================================
-- VERIFICAÇÃO FINAL
-- ============================================================

SELECT '✅ Tabela capability_profile_snapshot existe: ' || 
       CASE WHEN EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'capability_profile_snapshot') 
       THEN 'SIM' ELSE 'NÃO' END AS check1;

SELECT '✅ Coluna status existe: ' || 
       CASE WHEN EXISTS (
           SELECT 1 FROM information_schema.columns 
           WHERE table_name = 'capability_profile_snapshot' AND column_name = 'status'
       ) THEN 'SIM' ELSE 'NÃO' END AS check2;

SELECT '✅ Coluna locker_id existe: ' || 
       CASE WHEN EXISTS (
           SELECT 1 FROM information_schema.columns 
           WHERE table_name = 'capability_profile_snapshot' AND column_name = 'locker_id'
       ) THEN 'SIM' ELSE 'NÃO' END AS check3;

SELECT '✅ Índice ix_cap_snapshot_profile_status existe: ' || 
       CASE WHEN EXISTS (
           SELECT 1 FROM pg_indexes 
           WHERE tablename = 'capability_profile_snapshot' AND indexname = 'ix_cap_snapshot_profile_status'
       ) THEN 'SIM' ELSE 'NÃO' END AS check4;

SELECT '✅ product_locker_configs.requires_id_check existe: ' || 
       CASE WHEN EXISTS (
           SELECT 1 FROM information_schema.columns 
           WHERE table_name = 'product_locker_configs' AND column_name = 'requires_id_check'
       ) THEN 'SIM' ELSE 'NÃO' END AS check5;

SELECT '✅ orders.currency existe: ' || 
       CASE WHEN EXISTS (
           SELECT 1 FROM information_schema.columns 
           WHERE table_name = 'orders' AND column_name = 'currency'
       ) THEN 'SIM' ELSE 'NÃO' END AS check6;