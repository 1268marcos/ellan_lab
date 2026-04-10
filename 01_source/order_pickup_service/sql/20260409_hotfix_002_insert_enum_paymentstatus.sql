-- Adicionar um valor por vez
-- ALTER TYPE paymentstatus ADD VALUE 'REFUNDED';
-- ALTER TYPE paymentstatus ADD VALUE 'PARTIALLY_REFUNDED';
-- ALTER TYPE paymentstatus ADD VALUE 'AUTHORIZED';

-- ou --

DO $$
BEGIN
    -- Verificar se o valor já existe antes de adicionar
    IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumtypid = 'paymentstatus'::regtype AND enumlabel = 'REFUNDED') THEN
        ALTER TYPE paymentstatus ADD VALUE 'REFUNDED';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumtypid = 'paymentstatus'::regtype AND enumlabel = 'PARTIALLY_REFUNDED') THEN
        ALTER TYPE paymentstatus ADD VALUE 'PARTIALLY_REFUNDED';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumtypid = 'paymentstatus'::regtype AND enumlabel = 'AUTHORIZED') THEN
        ALTER TYPE paymentstatus ADD VALUE 'AUTHORIZED';
    END IF;
END $$;

-- Verificar o resultado
SELECT enum_range(NULL::paymentstatus);