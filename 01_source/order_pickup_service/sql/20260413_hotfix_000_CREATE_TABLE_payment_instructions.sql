-- 1. INSTRUÇÕES DE PAGAMENTO (Separa intenção vs execução)
CREATE TABLE public.payment_instructions (
    id VARCHAR(36) PRIMARY KEY,
    order_id VARCHAR NOT NULL REFERENCES public.orders(id),
    instruction_type VARCHAR(50) NOT NULL, -- 'AUTHORIZE_ONLY', 'CAPTURE_NOW', 'GENERATE_PIX', 'GENERATE_BOLETO', 'TOKENIZE'
    amount_cents INTEGER NOT NULL,
    currency VARCHAR(8) NOT NULL DEFAULT 'BRL',
    status VARCHAR(30) NOT NULL DEFAULT 'PENDING', -- 'PENDING', 'AUTHORIZED', 'CAPTURED', 'CANCELLED', 'EXPIRED'

    expires_at TIMESTAMP WITH TIME ZONE,
    qr_code TEXT, qr_code_text TEXT, barcode VARCHAR(255), digitable_line TEXT,

    authorization_code VARCHAR(100), capture_amount_cents INTEGER, captured_at TIMESTAMP WITH TIME ZONE,

    payment_token VARCHAR(255), customer_payment_method_id VARCHAR(36),

    wallet_provider VARCHAR(50), wallet_transaction_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
);
CREATE TRIGGER trg_pi_updated_at BEFORE UPDATE ON public.payment_instructions FOR EACH ROW EXECUTE FUNCTION public.set_row_updated_at();
CREATE INDEX ix_pi_order_id ON public.payment_instructions(order_id);
CREATE INDEX ix_pi_status_expires ON public.payment_instructions(status, expires_at) WHERE status = 'PENDING';
