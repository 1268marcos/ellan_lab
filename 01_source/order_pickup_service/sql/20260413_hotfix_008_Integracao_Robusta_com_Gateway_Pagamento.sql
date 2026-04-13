-- Integração Robusta com Gateway de Pagamento
ALTER TABLE public.payment_transactions 
    ADD COLUMN IF NOT EXISTS gateway_webhook_received_at TIMESTAMP WITH TIME ZONE,
    ADD COLUMN IF NOT EXISTS gateway_webhook_payload JSONB,
    ADD COLUMN IF NOT EXISTS acquirer_name VARCHAR(100),
    ADD COLUMN IF NOT EXISTS acquirer_message TEXT,
    ADD COLUMN IF NOT EXISTS tid VARCHAR(50),
    ADD COLUMN IF NOT EXISTS arqc VARCHAR(50),
    ADD COLUMN IF NOT EXISTS nsu_sitef VARCHAR(50),
    ADD COLUMN IF NOT EXISTS reconciliation_status VARCHAR(20) DEFAULT 'PENDING', -- 'PENDING', 'MATCHED', 'DISCREPANCY'
    ADD COLUMN IF NOT EXISTS reconciliation_batch_id VARCHAR(100);