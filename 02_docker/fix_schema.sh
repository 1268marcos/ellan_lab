#!/bin/bash
# fix_schema.sh

# chmod +x fix_schema.sh - dar permissão de execução

# Executar 
# ./fix_schema.sh

# Aguardar e verificar
# sleep 10


echo "=== Corrigindo schema do banco de dados ==="

# Extrair e executar partes do schema
docker exec -i postgres_central psql -U admin -d locker_central << 'EOF'
-- Primeiro, garantir que as tabelas principais existem com a estrutura correta
DO $$
BEGIN
    -- Verificar se a tabela orders existe
    IF NOT EXISTS (SELECT FROM pg_tables WHERE tablename = 'orders') THEN
        RAISE NOTICE 'Tabela orders não existe. Execute o schema completo primeiro.';
    ELSE
        -- Adicionar colunas faltantes na tabela orders
        ALTER TABLE orders ADD COLUMN IF NOT EXISTS site_id VARCHAR(100);
        ALTER TABLE orders ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(100);
        ALTER TABLE orders ADD COLUMN IF NOT EXISTS ecommerce_partner_id VARCHAR(100);
        ALTER TABLE orders ADD COLUMN IF NOT EXISTS partner_order_ref VARCHAR(255);
        ALTER TABLE orders ADD COLUMN IF NOT EXISTS sku_description TEXT;
        ALTER TABLE orders ADD COLUMN IF NOT EXISTS slot_size VARCHAR(20);
        ALTER TABLE orders ADD COLUMN IF NOT EXISTS card_brand VARCHAR(50);
        ALTER TABLE orders ADD COLUMN IF NOT EXISTS card_last4 VARCHAR(8);
        ALTER TABLE orders ADD COLUMN IF NOT EXISTS installments INTEGER;
        ALTER TABLE orders ADD COLUMN IF NOT EXISTS guest_name VARCHAR(255);
        ALTER TABLE orders ADD COLUMN IF NOT EXISTS consent_analytics BOOLEAN DEFAULT false;
        ALTER TABLE orders ADD COLUMN IF NOT EXISTS cancelled_at TIMESTAMPTZ;
        ALTER TABLE orders ADD COLUMN IF NOT EXISTS cancel_reason VARCHAR(255);
        ALTER TABLE orders ADD COLUMN IF NOT EXISTS refunded_at TIMESTAMPTZ;
        ALTER TABLE orders ADD COLUMN IF NOT EXISTS refund_reason VARCHAR(255);
        ALTER TABLE orders ADD COLUMN IF NOT EXISTS payment_interface VARCHAR(32);
        ALTER TABLE orders ADD COLUMN IF NOT EXISTS wallet_provider VARCHAR(64);
        ALTER TABLE orders ADD COLUMN IF NOT EXISTS device_id VARCHAR(128);
        ALTER TABLE orders ADD COLUMN IF NOT EXISTS ip_address VARCHAR(64);
        ALTER TABLE orders ADD COLUMN IF NOT EXISTS user_agent VARCHAR(500);
        ALTER TABLE orders ADD COLUMN IF NOT EXISTS idempotency_key VARCHAR(255);
        ALTER TABLE orders ADD COLUMN IF NOT EXISTS order_metadata JSONB;
        ALTER TABLE orders ADD COLUMN IF NOT EXISTS sku_id VARCHAR(255);
        ALTER TABLE orders ADD COLUMN IF NOT EXISTS payment_method VARCHAR(30);
        ALTER TABLE orders ADD COLUMN IF NOT EXISTS payment_status VARCHAR(20);
        ALTER TABLE orders ADD COLUMN IF NOT EXISTS payment_updated_at TIMESTAMPTZ;
        ALTER TABLE orders ADD COLUMN IF NOT EXISTS gateway_transaction_id VARCHAR(255);
        ALTER TABLE orders ADD COLUMN IF NOT EXISTS receipt_email VARCHAR(255);
        ALTER TABLE orders ADD COLUMN IF NOT EXISTS receipt_phone VARCHAR(255);
        ALTER TABLE orders ADD COLUMN IF NOT EXISTS guest_email VARCHAR(255);
        ALTER TABLE orders ADD COLUMN IF NOT EXISTS guest_phone VARCHAR(255);
        ALTER TABLE orders ADD COLUMN IF NOT EXISTS public_access_token_hash VARCHAR(255);
        ALTER TABLE orders ADD COLUMN IF NOT EXISTS consent_marketing INTEGER DEFAULT 0;
        ALTER TABLE orders ADD COLUMN IF NOT EXISTS card_type VARCHAR(10);
        ALTER TABLE orders ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();
        
        RAISE NOTICE 'Colunas adicionadas/verificadas na tabela orders';
    END IF;
END $$;

-- Verificar e criar a tabela pickup_tokens com a estrutura correta
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_tables WHERE tablename = 'pickup_tokens') THEN
        CREATE TABLE pickup_tokens (
            id VARCHAR NOT NULL PRIMARY KEY,
            pickup_id VARCHAR NOT NULL,
            token_hash VARCHAR NOT NULL,
            expires_at TIMESTAMPTZ NOT NULL,
            used_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL,
            is_active BOOLEAN DEFAULT true,
            manual_code VARCHAR,
            manual_code_encrypted VARCHAR
        );
        RAISE NOTICE 'Tabela pickup_tokens criada';
    ELSE
        -- Adicionar colunas faltantes
        ALTER TABLE pickup_tokens ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true;
        ALTER TABLE pickup_tokens ADD COLUMN IF NOT EXISTS manual_code VARCHAR;
        ALTER TABLE pickup_tokens ADD COLUMN IF NOT EXISTS manual_code_encrypted VARCHAR;
        RAISE NOTICE 'Colunas verificadas na tabela pickup_tokens';
    END IF;
END $$;

-- Criar índices necessários
CREATE INDEX IF NOT EXISTS idx_pickup_tokens_pickup_id ON pickup_tokens(pickup_id);
CREATE INDEX IF NOT EXISTS idx_pickup_tokens_token_hash ON pickup_tokens(token_hash);
CREATE INDEX IF NOT EXISTS idx_pickup_tokens_expires_at ON pickup_tokens(expires_at) WHERE is_active = true;

-- Recarregar configuração
SELECT pg_reload_conf();

EOF

echo "=== Correção concluída ==="