-- 4. MOVIMENTAÇÕES DA WALLET (Double-Entry auditável)
CREATE TABLE public.wallet_transactions (
    id VARCHAR(36) PRIMARY KEY,
    wallet_id VARCHAR(36) NOT NULL REFERENCES public.user_wallets(id),
    order_id VARCHAR REFERENCES public.orders(id),
    type VARCHAR(30) NOT NULL, -- 'DEPOSIT', 'WITHDRAWAL', 'PAYMENT', 'REFUND', 'CASHBACK', 'ADJUSTMENT'
    amount_cents BIGINT NOT NULL,
    balance_after_cents BIGINT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    external_reference VARCHAR(255), description TEXT, metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
);
CREATE INDEX ix_wt_wallet ON public.wallet_transactions(wallet_id, created_at DESC);
CREATE INDEX ix_wt_order ON public.wallet_transactions(order_id);