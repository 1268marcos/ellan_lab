CREATE TABLE IF NOT EXISTS public.saved_payment_methods (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    method_code VARCHAR(80) NOT NULL,
    gateway_token VARCHAR(255) NOT NULL,
    last4 VARCHAR(4),
    card_brand VARCHAR(50),
    cardholder_name VARCHAR(255),
    expiry_month INTEGER,
    expiry_year INTEGER,
    is_default BOOLEAN NOT NULL DEFAULT false,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),

    CONSTRAINT fk_spm_user
        FOREIGN KEY (user_id)
        REFERENCES public.users(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_spm_method_code
        FOREIGN KEY (method_code)
        REFERENCES public.payment_method_catalog(code)
        ON DELETE CASCADE
);

CREATE TRIGGER trg_spm_updated_at
BEFORE UPDATE ON public.saved_payment_methods
FOR EACH ROW
EXECUTE FUNCTION public.set_row_updated_at();

CREATE INDEX IF NOT EXISTS ix_spm_user_active
ON public.saved_payment_methods(user_id, is_active);

CREATE UNIQUE INDEX IF NOT EXISTS uq_user_default_method
ON public.saved_payment_methods(user_id)
WHERE is_default = true;