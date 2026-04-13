-- 6. ALTERAÇÕES EM TABELAS EXISTENTES
ALTER TABLE public.lockers ADD COLUMN payment_rules JSONB DEFAULT '{"allowed_methods": [], "minimum_amount_cents": 0, "payment_instruction": "CAPTURE_NOW", "cash_allowed": false, "wallet_allowed": true}'::jsonb;

ALTER TABLE public.payment_transactions ADD COLUMN gateway_webhook_received_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE public.payment_transactions ADD COLUMN gateway_webhook_payload JSONB;
ALTER TABLE public.payment_transactions ADD COLUMN acquirer_name VARCHAR(100);
ALTER TABLE public.payment_transactions ADD COLUMN acquirer_message TEXT;
ALTER TABLE public.payment_transactions ADD COLUMN tid VARCHAR(50);
ALTER TABLE public.payment_transactions ADD COLUMN arqc VARCHAR(50);
ALTER TABLE public.payment_transactions ADD COLUMN nsu_sitef VARCHAR(50);
ALTER TABLE public.payment_transactions ADD COLUMN reconciliation_status VARCHAR(20) DEFAULT 'PENDING' NOT NULL;
ALTER TABLE public.payment_transactions ADD COLUMN reconciliation_batch_id VARCHAR(100);

CREATE INDEX ix_pt_reconciliation ON public.payment_transactions(reconciliation_status) WHERE reconciliation_status = 'PENDING';
CREATE INDEX ix_pt_webhook_pending ON public.payment_transactions(gateway_webhook_received_at) WHERE gateway_webhook_received_at IS NULL;