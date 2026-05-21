-- Patches idempotentes: colunas que serviços (order_pickup, payment_gateway) esperam.
-- Seguro após 03_tables.sql — usa IF NOT EXISTS.
-- Se o dump já incluir a coluna, estes ALTER são no-op.

BEGIN;

-- orders (fix_schema.sh / apps)
ALTER TABLE public.orders ADD COLUMN IF NOT EXISTS site_id VARCHAR(100);
ALTER TABLE public.orders ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(100);
ALTER TABLE public.orders ADD COLUMN IF NOT EXISTS ecommerce_partner_id VARCHAR(100);
ALTER TABLE public.orders ADD COLUMN IF NOT EXISTS partner_order_ref VARCHAR(255);
ALTER TABLE public.orders ADD COLUMN IF NOT EXISTS sku_description TEXT;
ALTER TABLE public.orders ADD COLUMN IF NOT EXISTS slot_size VARCHAR(20);
ALTER TABLE public.orders ADD COLUMN IF NOT EXISTS card_brand VARCHAR(50);
ALTER TABLE public.orders ADD COLUMN IF NOT EXISTS card_last4 VARCHAR(8);
ALTER TABLE public.orders ADD COLUMN IF NOT EXISTS installments INTEGER;
ALTER TABLE public.orders ADD COLUMN IF NOT EXISTS guest_name VARCHAR(255);
ALTER TABLE public.orders ADD COLUMN IF NOT EXISTS consent_analytics BOOLEAN DEFAULT false;
ALTER TABLE public.orders ADD COLUMN IF NOT EXISTS cancelled_at TIMESTAMPTZ;
ALTER TABLE public.orders ADD COLUMN IF NOT EXISTS cancel_reason VARCHAR(255);
ALTER TABLE public.orders ADD COLUMN IF NOT EXISTS refunded_at TIMESTAMPTZ;
ALTER TABLE public.orders ADD COLUMN IF NOT EXISTS refund_reason VARCHAR(255);
ALTER TABLE public.orders ADD COLUMN IF NOT EXISTS payment_interface VARCHAR(32);
ALTER TABLE public.orders ADD COLUMN IF NOT EXISTS wallet_provider VARCHAR(64);
ALTER TABLE public.orders ADD COLUMN IF NOT EXISTS device_id VARCHAR(128);
ALTER TABLE public.orders ADD COLUMN IF NOT EXISTS ip_address VARCHAR(64);
ALTER TABLE public.orders ADD COLUMN IF NOT EXISTS user_agent VARCHAR(500);
ALTER TABLE public.orders ADD COLUMN IF NOT EXISTS idempotency_key VARCHAR(255);
ALTER TABLE public.orders ADD COLUMN IF NOT EXISTS order_metadata JSONB;
ALTER TABLE public.orders ADD COLUMN IF NOT EXISTS sku_id VARCHAR(255);
ALTER TABLE public.orders ADD COLUMN IF NOT EXISTS payment_method VARCHAR(30);
ALTER TABLE public.orders ADD COLUMN IF NOT EXISTS payment_status VARCHAR(20);
ALTER TABLE public.orders ADD COLUMN IF NOT EXISTS payment_updated_at TIMESTAMPTZ;
ALTER TABLE public.orders ADD COLUMN IF NOT EXISTS gateway_transaction_id VARCHAR(255);
ALTER TABLE public.orders ADD COLUMN IF NOT EXISTS receipt_email VARCHAR(255);
ALTER TABLE public.orders ADD COLUMN IF NOT EXISTS receipt_phone VARCHAR(255);
ALTER TABLE public.orders ADD COLUMN IF NOT EXISTS guest_email VARCHAR(255);
ALTER TABLE public.orders ADD COLUMN IF NOT EXISTS guest_phone VARCHAR(255);
ALTER TABLE public.orders ADD COLUMN IF NOT EXISTS public_access_token_hash VARCHAR(255);
ALTER TABLE public.orders ADD COLUMN IF NOT EXISTS consent_marketing INTEGER DEFAULT 0;
ALTER TABLE public.orders ADD COLUMN IF NOT EXISTS card_type VARCHAR(10);
ALTER TABLE public.orders ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

-- pickup_tokens
ALTER TABLE public.pickup_tokens ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true;
ALTER TABLE public.pickup_tokens ADD COLUMN IF NOT EXISTS manual_code VARCHAR;
ALTER TABLE public.pickup_tokens ADD COLUMN IF NOT EXISTS manual_code_encrypted VARCHAR;

COMMIT;
