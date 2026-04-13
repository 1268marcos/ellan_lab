-- 3. WALLET DO USUÁRIO (Saldo recarregável)
CREATE TABLE public.user_wallets (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) UNIQUE NOT NULL REFERENCES public.users(id),
    balance_cents BIGINT NOT NULL DEFAULT 0,
    currency VARCHAR(8) NOT NULL DEFAULT 'BRL',
    status VARCHAR(20) DEFAULT 'ACTIVE' NOT NULL,
    last_transaction_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
);
CREATE TRIGGER trg_uw_updated_at BEFORE UPDATE ON public.user_wallets FOR EACH ROW EXECUTE FUNCTION public.set_row_updated_at();
