-- 5. SPLIT DE PAGAMENTO (Marketplace/Operadores)
CREATE TABLE public.payment_splits (
    id VARCHAR(36) PRIMARY KEY,
    order_id VARCHAR NOT NULL REFERENCES public.orders(id),
    recipient_type VARCHAR(30) NOT NULL, -- 'LOCKER_OPERATOR', 'ECOMMERCE_PARTNER', 'LOGISTICS', 'PLATFORM'
    recipient_id VARCHAR NOT NULL,
    amount_cents INTEGER NOT NULL,
    percentage DECIMAL(5,2),
    status VARCHAR(20) DEFAULT 'PENDING' NOT NULL,
    settled_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
);
CREATE INDEX ix_ps_order ON public.payment_splits(order_id);
CREATE INDEX ix_ps_recipient ON public.payment_splits(recipient_type, recipient_id, status);
