-- ============================================================
-- HOTFIX COMPLETO - product_categories com unidades corretas
-- ============================================================

DO $$
BEGIN
    RAISE NOTICE '=== CORRIGINDO product_categories (unidades: mm e g) ===';
    
    -- Garantir que TODAS as colunas existam com os tipos corretos
    BEGIN
        -- Colunas principais
        ALTER TABLE product_categories ADD COLUMN IF NOT EXISTS max_weight_g INTEGER;
        ALTER TABLE product_categories ADD COLUMN IF NOT EXISTS max_width_mm INTEGER;
        ALTER TABLE product_categories ADD COLUMN IF NOT EXISTS max_height_mm INTEGER;
        ALTER TABLE product_categories ADD COLUMN IF NOT EXISTS max_depth_mm INTEGER;
        
        -- Colunas de configuração
        ALTER TABLE product_categories ADD COLUMN IF NOT EXISTS default_temperature_zone VARCHAR(32) NOT NULL DEFAULT 'AMBIENT';
        ALTER TABLE product_categories ADD COLUMN IF NOT EXISTS default_security_level VARCHAR(32) NOT NULL DEFAULT 'STANDARD';
        ALTER TABLE product_categories ADD COLUMN IF NOT EXISTS is_hazardous BOOLEAN NOT NULL DEFAULT FALSE;
        ALTER TABLE product_categories ADD COLUMN IF NOT EXISTS requires_age_verification BOOLEAN NOT NULL DEFAULT FALSE;
        
        RAISE NOTICE '✅ Colunas garantidas com unidades mm/g';
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE '⚠️ Erro ao adicionar colunas: %', SQLERRM;
    END;
    
    -- Verificar resultado
    RAISE NOTICE '=== VERIFICAÇÃO FINAL ===';
END $$;

-- Mostrar todas as colunas após correção
SELECT column_name, data_type, is_nullable
FROM information_schema.columns 
WHERE table_name = 'product_categories'
ORDER BY column_name;