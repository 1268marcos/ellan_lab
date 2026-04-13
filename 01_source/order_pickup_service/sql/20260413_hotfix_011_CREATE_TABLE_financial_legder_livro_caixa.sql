-- 1. Financial Ledger (Livro-Razão Imutável)
-- Substitua a leitura de orders.amount_cents para relatórios financeiros 
-- por consultas a esta tabela. Nunca atualize ou 
-- delete registros. Em caso de estorno, crie uma linha VOID ou REFUND.

CREATE TABLE public.financial_ledger (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    order_id VARCHAR(36) REFERENCES public.orders(id),
    payment_transaction_id VARCHAR(36) REFERENCES public.payment_transactions(id),
    wallet_id VARCHAR(36) REFERENCES public.user_wallets(id),
    entry_type VARCHAR(30) NOT NULL, -- 'CAPTURE', 'AUTH_HOLD', 'REFUND', 'CHARGEBACK', 'FEE', 'SPLIT_PAYOUT', 'WALLET_DEBIT', 'WALLET_CREDIT'
    amount_cents BIGINT NOT NULL,
    currency VARCHAR(8) NOT NULL DEFAULT 'BRL',
    status VARCHAR(20) NOT NULL DEFAULT 'POSTED', -- 'PENDING', 'POSTED', 'VOIDED'
    external_reference VARCHAR(100), -- NSU, AR, Gateway ID
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
);

-- Regra de ouro: Ledger é append-only
ALTER TABLE public.financial_ledger ADD CONSTRAINT ck_ledger_amount_nonzero CHECK (amount_cents != 0);
ALTER TABLE public.financial_ledger ADD CONSTRAINT ck_ledger_status_check CHECK (status IN ('PENDING','POSTED','VOIDED'));

CREATE INDEX ix_ledger_order ON public.financial_ledger(order_id);
CREATE INDEX ix_ledger_type_status ON public.financial_ledger(entry_type, status);
CREATE INDEX ix_ledger_created ON public.financial_ledger(created_at DESC);
